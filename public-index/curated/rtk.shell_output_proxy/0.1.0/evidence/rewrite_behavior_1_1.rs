//! Translates a raw shell command into its RTK-optimized equivalent.

use super::permissions::{check_command, PermissionVerdict};
use crate::discover::registry;
use std::io::Write;

/// Run the `rtk rewrite` command.
///
/// Prints the RTK-rewritten command to stdout and exits with a code that tells
/// the caller how to handle permissions:
///
/// | Exit | Stdout   | Meaning                                                      |
/// |------|----------|--------------------------------------------------------------|
/// | 0    | rewritten| Rewrite allowed — hook may auto-allow the rewritten command. |
/// | 1    | (none)   | No RTK equivalent — hook passes through unchanged.           |
/// | 2    | (none)   | Deny rule matched — hook defers to Claude Code native deny.  |
/// | 3    | rewritten| Ask rule matched — hook rewrites but lets Claude Code prompt.|
pub fn run(cmd: &str) -> anyhow::Result<()> {
    let (excluded, transparent_prefixes) = crate::core::config::Config::load()
        .map(|c| (c.hooks.exclude_commands, c.hooks.transparent_prefixes))
        .unwrap_or_default();

    match evaluate(cmd, &excluded, &transparent_prefixes) {
        RewriteOutcome::Allow(rewritten) => {
            print!("{}", rewritten);
            let _ = std::io::stdout().flush();
            Ok(())
        }
        RewriteOutcome::Ask(rewritten) => {
            print!("{}", rewritten);
            let _ = std::io::stdout().flush();
            std::process::exit(3);
        }
        RewriteOutcome::Deny => std::process::exit(2),
        RewriteOutcome::Passthrough => std::process::exit(1),
    }
}

#[derive(Debug, PartialEq)]
enum RewriteOutcome {
    Allow(String),
    Passthrough,
    Deny,
    Ask(String),
}

fn evaluate(cmd: &str, excluded: &[String], transparent_prefixes: &[String]) -> RewriteOutcome {
    let verdict = check_command(cmd);

    if verdict == PermissionVerdict::Deny {
        return RewriteOutcome::Deny;
    }

    if crate::discover::lexer::contains_unattestable_construct(cmd) {
        return RewriteOutcome::Passthrough;
    }

    match registry::rewrite_command(cmd, excluded, transparent_prefixes) {
        Some(rewritten) => match verdict {
            PermissionVerdict::Allow => RewriteOutcome::Allow(rewritten),
            _ => RewriteOutcome::Ask(rewritten),
        },
        None => RewriteOutcome::Passthrough,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn rewrite_command_no_prefixes(cmd: &str) -> Option<String> {
        registry::rewrite_command(cmd, &[], &[])
    }

    #[test]
    fn test_run_supported_command_succeeds() {
        assert!(rewrite_command_no_prefixes("git status").is_some());
    }

    #[test]
