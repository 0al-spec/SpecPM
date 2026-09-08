class CodexClient:
    """Synchronous typed JSON-RPC client for `codex app-server` over stdio."""

    def __init__(
        self,
        config: CodexConfig | None = None,
        approval_handler: ApprovalHandler | None = None,
    ) -> None:
        self.config = config or CodexConfig()
        self._approval_handler = approval_handler or self._default_approval_handler
        self._proc: subprocess.Popen[str] | None = None
        self._lock = threading.Lock()
        self._thread_start_locks_guard = threading.Lock()
        self._thread_start_locks: dict[str, _ThreadStartLock] = {}
        self._router = MessageRouter()
        self._stderr_lines: deque[str] = deque(maxlen=400)
        self._stderr_thread: threading.Thread | None = None
        self._reader_thread: threading.Thread | None = None

    def __enter__(self) -> "CodexClient":
        self.start()
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        self.close()

    def start(self) -> None:
        if self._proc is not None:
            return

        path_dirs: tuple[Path, ...] = ()
        if self.config.launch_args_override is not None:
            args = list(self.config.launch_args_override)
        else:
            codex_bin = _resolve_codex_bin(self.config)
            if self.config.codex_bin is None:
                path_dirs = _installed_codex_path_dirs()
            args = [str(codex_bin)]
            for kv in self.config.config_overrides:
                args.extend(["--config", kv])
            args.extend(["app-server", "--listen", "stdio://"])

        env = os.environ.copy()
        if self.config.env:
            env.update(self.config.env)
        _prepend_path_dirs(env, path_dirs)

        self._proc = subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            cwd=self.config.cwd,
            env=env,
            bufsize=1,
        )
