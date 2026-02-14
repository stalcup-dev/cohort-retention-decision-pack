from __future__ import annotations

import os
import platform
import struct
import subprocess
import sys


def main() -> None:
    bits = struct.calcsize("P") * 8
    print(f"python_version={sys.version.split()[0]}")
    print(f"python_bits={bits}")
    print(f"python_machine={platform.machine()}")
    print(f"python_executable={sys.executable}")
    print(f"PIP_NO_INDEX={os.environ.get('PIP_NO_INDEX', '<unset>')}")
    print(f"HTTPS_PROXY={os.environ.get('HTTPS_PROXY', '<unset>')}")

    if bits != 64:
        print("ERROR: 32-bit Python detected. Use 64-bit Python to install ruff wheels.")
        raise SystemExit(1)

    probe = subprocess.run(
        [sys.executable, "-m", "pip", "index", "versions", "ruff"],
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode == 0:
        print("ruff_index_probe=PASS")
        return

    print("ruff_index_probe=FAIL")
    print(probe.stdout.strip())
    print(probe.stderr.strip())
    print(
        "Ruff install is blocked in this environment. "
        "Use CI source-of-truth workflow at .github/workflows/ci.yml "
        "with: pip install -e \".[dev]\", ruff check ., pytest -q, python scripts/smoke_pipeline.py."
    )
    raise SystemExit(2)


if __name__ == "__main__":
    main()
