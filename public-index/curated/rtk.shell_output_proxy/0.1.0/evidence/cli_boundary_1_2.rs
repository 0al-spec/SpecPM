        args: Vec<String>,
    },

    /// Show hook rewrite audit metrics (requires RTK_HOOK_AUDIT=1)
    #[command(name = "hook-audit")]
    HookAudit {
        /// Show entries from last N days (0 = all time)
        #[arg(short, long, default_value = "7")]
        since: u64,
    },

    /// Rewrite a raw command to its RTK equivalent (single source of truth for hooks)
    ///
    /// Exits 0 and prints the rewritten command if supported.
    /// Exits 1 with no output if the command has no RTK equivalent.
    ///
    /// Used by Claude Code, Gemini CLI, and other LLM hooks:
    ///   REWRITTEN=$(rtk rewrite "$CMD") || exit 0
    Rewrite {
        /// Raw command to rewrite (e.g. "git status", "cargo test && git push")
        /// Accepts multiple args: `rtk rewrite ls -al` is equivalent to `rtk rewrite "ls -al"`
        #[arg(trailing_var_arg = true, allow_hyphen_values = true)]
        args: Vec<String>,
    },

    /// Hook processors for LLM CLI tools (Gemini CLI, Copilot, etc.)
    Hook {
        #[command(subcommand)]
        command: HookCommands,
    },
}
