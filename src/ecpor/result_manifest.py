"""Compatibility wrapper for result manifest builders and CLI.

The implementation is split across manifest_common, manifest_builders, and
manifest_cli. This module keeps the old `ecpor.result_manifest` import path and
`python -m ecpor.result_manifest ...` command stable.
"""

from __future__ import annotations

from .manifest_builders import *  # noqa: F401,F403
from .manifest_cli import main
from .manifest_common import build_result_manifest, write_manifest


if __name__ == "__main__":
    raise SystemExit(main())
