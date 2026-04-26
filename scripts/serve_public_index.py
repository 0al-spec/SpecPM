#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from specpm.public_index import generate_public_index


def main() -> int:
    port = int(os.environ.get("SPECPM_PUBLIC_INDEX_PORT", "8081"))
    registry_url = os.environ.get("SPECPM_PUBLIC_INDEX_REGISTRY_URL") or (
        f"http://localhost:{port}"
    )
    output_dir = Path(os.environ.get("SPECPM_PUBLIC_INDEX_OUTPUT", ".specpm/public-index"))
    package_dir = Path(os.environ.get("SPECPM_PUBLIC_INDEX_PACKAGE", "examples/email_tools"))

    report = generate_public_index([package_dir], output_dir, registry_url)
    print(json.dumps(report, indent=2, sort_keys=True), flush=True)
    if report["status"] != "ok":
        return 1

    handler = partial(SimpleHTTPRequestHandler, directory=str(output_dir))
    server = ThreadingHTTPServer(("0.0.0.0", 8081), handler)
    print(f"serving SpecPM public index at {registry_url}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
