"""Launch the API server.

Usage::

    python serve.py            # http://127.0.0.1:8000
    python serve.py --port 9000 --reload

``uvicorn`` is started via ``uvicorn.run`` rather than the ``uvicorn`` console
script because this environment cannot write ``.exe`` shims into Python's
``Scripts`` directory (pip fails with WinError 2 on every console-script install).
The package itself imports and runs correctly.
"""
from __future__ import annotations

import argparse
import os
import sys

# Allow `python serve.py` from the repo root without installing the package.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the AI Buying Assistant API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    try:
        import uvicorn
    except ImportError:
        print(
            "uvicorn is not installed.\n"
            "Install it with:\n"
            "  python -m pip install --no-deps fastapi starlette uvicorn click sniffio",
            file=sys.stderr,
        )
        return 1

    print(f"API  ->  http://{args.host}:{args.port}/api/health")
    print(f"Docs ->  http://{args.host}:{args.port}/docs")
    uvicorn.run(
        "aba.api.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())