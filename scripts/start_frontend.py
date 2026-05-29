from __future__ import annotations

import subprocess


def main() -> int:
    print("Starting frontend dev server")
    return subprocess.call(["npm", "run", "dev"], cwd="frontend")


if __name__ == "__main__":
    raise SystemExit(main())
