        /// Minimum occurrences to include in report
        #[arg(long, default_value = "1")]
        min_occurrences: usize,
    },

    /// Execute a shell command via sh -c (raw, no filtering or tracking)
    Run {
        /// Command string to execute (use -c for shell-like invocation)
        #[arg(short = 'c', long = "command")]
        command: Option<String>,
        /// Positional command arguments (alternative to -c)
        #[arg(trailing_var_arg = true, allow_hyphen_values = true)]
        args: Vec<String>,
    },

    /// Execute command without filtering but track usage
    Proxy {
        /// Command and arguments to execute
        #[arg(trailing_var_arg = true, allow_hyphen_values = true)]
        args: Vec<OsString>,
    },

    /// Read stdin, apply filter, print filtered output (Unix pipe mode)
    Pipe {
        /// Filter name (cargo-test, pytest, phpunit, phpstan, pint, grep, find, git-log, etc.)
        #[arg(short, long)]
        filter: Option<String>,

        /// Pass stdin through without filtering
        #[arg(long)]
        passthrough: bool,
    },

    /// Trust project-local TOML filters in current directory
    Trust {
        /// List all trusted filter files
