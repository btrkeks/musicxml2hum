#!/usr/bin/env python3
"""Regenerate expected Humdrum outputs for the MusicXML fixtures."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = REPO_ROOT / "tests"
EXPECTED_DIR = TESTS_DIR / "expected"
DEFAULT_BINARY = REPO_ROOT / "build" / "debug" / "musicxml2hum"


def converter_env() -> dict[str, str]:
    env = os.environ.copy()
    if env.get("MUSICXML2HUM_DETECT_LEAKS") == "1":
        return env

    asan_options = env.get("ASAN_OPTIONS")
    options = [] if not asan_options else [
        option for option in asan_options.split(":") if not option.startswith("detect_leaks=")
    ]
    options.append("detect_leaks=0")
    env["ASAN_OPTIONS"] = ":".join(options)
    return env


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Regenerate tests/expected/*.krn from tests/*.xml."
    )
    parser.add_argument(
        "--binary",
        type=Path,
        default=DEFAULT_BINARY,
        help="musicxml2hum binary to use (default: build/debug/musicxml2hum)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    binary = args.binary.resolve()

    if not binary.is_file():
        print(f"error: binary not found: {binary}", file=sys.stderr)
        return 1

    xml_files = sorted(TESTS_DIR.glob("*.xml"))
    if not xml_files:
        print(f"error: no XML fixtures found in {TESTS_DIR}", file=sys.stderr)
        return 1

    EXPECTED_DIR.mkdir(parents=True, exist_ok=True)

    expected_names = {xml_file.with_suffix(".krn").name for xml_file in xml_files}
    for stale in EXPECTED_DIR.glob("*.krn"):
        if stale.name not in expected_names:
            stale.unlink()

    for xml_file in xml_files:
        expected_file = EXPECTED_DIR / xml_file.with_suffix(".krn").name
        result = subprocess.run(
            [str(binary), str(xml_file)],
            cwd=REPO_ROOT,
            env=converter_env(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode != 0:
            sys.stderr.buffer.write(result.stderr)
            print(f"error: conversion failed for {xml_file.name}", file=sys.stderr)
            return result.returncode
        expected_file.write_bytes(result.stdout)
        print(f"updated {expected_file.relative_to(REPO_ROOT)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
