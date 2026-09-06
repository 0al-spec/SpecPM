            if raw.trim().is_empty() {
                0
            } else {
                use std::process::Command as ProcCommand;
                let shell = if cfg!(windows) { "cmd" } else { "sh" };
                let flag = if cfg!(windows) { "/C" } else { "-c" };
                let status = ProcCommand::new(shell)
                    .arg(flag)
                    .arg(&raw)
                    .status()
                    .with_context(|| format!("Failed to execute: {}", raw))?;
                core::utils::exit_code_from_status(&status, "run")
            }
        }

        Commands::Proxy { args } => {
            use std::io::{Read, Write};
            use std::process::Stdio;
            use std::sync::atomic::{AtomicU32, Ordering};
            use std::thread;

            if args.is_empty() {
                anyhow::bail!(
                    "proxy requires a command to execute\nUsage: rtk proxy <command> [args...]"
                );
            }

            let timer = core::tracking::TimedExecution::start();

            // If a single quoted arg contains spaces, split it respecting quotes (#388).
            // e.g. rtk proxy 'head -50 file.php' → cmd=head, args=["-50", "file.php"]
            // e.g. rtk proxy 'git log --format="%H %s"' → cmd=git, args=["log", "--format=%H %s"]
            let (cmd_name, cmd_args): (String, Vec<String>) = if args.len() == 1 {
                let full = args[0].to_string_lossy();
                let parts = shell_split(&full);
                if parts.len() > 1 {
                    (parts[0].clone(), parts[1..].to_vec())
                } else {
                    (full.into_owned(), vec![])
                }
            } else {
