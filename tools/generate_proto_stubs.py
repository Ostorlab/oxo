"""Regenerate protobuf type stubs without replacing runtime protobuf modules."""

from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys


def main() -> None:
    """Generate stubs for each schema using the pinned typing dependencies."""
    project_root = pathlib.Path(__file__).resolve().parents[1]
    source_root = project_root / "src"
    plugin = shutil.which("protoc-gen-mypy")
    if plugin is None:
        raise RuntimeError(
            "Install typing_requirements.txt to generate protobuf stubs."
        )
    for schema in sorted((source_root / "ostorlab").rglob("*.proto")):
        if "KB" in schema.relative_to(source_root).parts:
            continue
        subprocess.run(
            [
                sys.executable,
                "-m",
                "grpc_tools.protoc",
                f"-I{source_root}",
                f"--plugin=protoc-gen-mypy={plugin}",
                f"--mypy_out={source_root}",
                str(schema),
            ],
            check=True,
            cwd=project_root,
        )


if __name__ == "__main__":
    main()
