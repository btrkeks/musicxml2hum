from __future__ import annotations

import difflib
import os
import re
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = REPO_ROOT / "tests"
EXPECTED_DIR = TESTS_DIR / "expected"
DEFAULT_BINARY = REPO_ROOT / "build" / "debug" / "musicxml2hum"


def musicxml2hum_binary() -> Path:
    return Path(os.environ.get("MUSICXML2HUM_BINARY", DEFAULT_BINARY)).resolve()


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


def xml_fixtures() -> list[Path]:
    return sorted(TESTS_DIR.glob("*.xml"))


@pytest.fixture(scope="session")
def binary() -> Path:
    binary_path = musicxml2hum_binary()
    if not binary_path.is_file():
        pytest.fail(
            f"musicxml2hum binary not found at {binary_path}; run `make debug` first"
        )
    return binary_path


def run_converter(binary: Path, xml_file: Path) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [str(binary), str(xml_file)],
        cwd=REPO_ROOT,
        env=converter_env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def text_diff(expected: bytes, actual: bytes, expected_name: str, actual_name: str) -> str:
    expected_text = expected.decode("utf-8", errors="replace").splitlines(keepends=True)
    actual_text = actual.decode("utf-8", errors="replace").splitlines(keepends=True)
    return "".join(
        difflib.unified_diff(
            expected_text,
            actual_text,
            fromfile=expected_name,
            tofile=actual_name,
        )
    )


@pytest.mark.parametrize("xml_file", xml_fixtures(), ids=lambda path: path.stem)
def test_conversion_matches_golden(binary: Path, xml_file: Path) -> None:
    expected_file = EXPECTED_DIR / xml_file.with_suffix(".krn").name
    assert expected_file.is_file(), (
        f"missing golden file for {xml_file.name}; run `make update-goldens`"
    )

    result = run_converter(binary, xml_file)
    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")

    expected = expected_file.read_bytes()
    if result.stdout != expected:
        diff = text_diff(
            expected,
            result.stdout,
            str(expected_file.relative_to(REPO_ROOT)),
            f"actual/{xml_file.with_suffix('.krn').name}",
        )
        pytest.fail(f"{xml_file.name} output differs from golden\n{diff}")


def assert_contains(output: bytes, needle: bytes) -> None:
    assert needle in output, f"missing expected output fragment: {needle!r}"


def assert_not_contains(output: bytes, needle: bytes) -> None:
    assert needle not in output, f"unexpected output fragment: {needle!r}"


def assert_stderr_not_matches(stderr: bytes, pattern: bytes) -> None:
    assert re.search(pattern, stderr) is None, (
        "unexpected stderr pattern "
        f"{pattern!r} in {stderr.decode('utf-8', errors='replace')}"
    )


def assert_regression(binary: Path, fixture_name: str) -> subprocess.CompletedProcess[bytes]:
    result = run_converter(binary, TESTS_DIR / fixture_name)
    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    return result


def test_leading_equals_lyrics(binary: Path) -> None:
    result = assert_regression(binary, "leading_equals_lyrics.xml")

    assert_contains(result.stdout, "4g\t\\=A-\tHear".encode())
    assert_contains(result.stdout, "4a\t\\=cevs\t.".encode())
    assert_contains(result.stdout, "4b\t\\= E\t.".encode())
    assert_contains(result.stdout, "4cc\t\\=\u00a0E\t.".encode())
    assert re.search(rb"(?m)^[^=\t][^\t]*\t=", result.stdout) is None


def test_hidden_extra_voice_rest_spine(binary: Path) -> None:
    result = assert_regression(binary, "hidden_extra_voice_rest_spine.xml")

    assert_stderr_not_matches(
        result.stderr, rb"Expected [0-9]+ fields|spine [0-9]+ is not terminated"
    )
    assert_contains(result.stdout, b"*^")
    assert_contains(result.stdout, b"*v")


def test_final_measure_split_voice_merge(binary: Path) -> None:
    result = assert_regression(binary, "final_measure_split_voice_merge.xml")

    assert_stderr_not_matches(
        result.stderr, rb"Expected [0-9]+ fields|spine [0-9]+ is not terminated"
    )
    assert_contains(result.stdout, b"*\t*v\t*v\t*")
    assert_contains(result.stdout, b"==\t==\t==")
    assert_contains(result.stdout, b"*-\t*-\t*-")


def test_forward_gap_secondary_voice(binary: Path) -> None:
    result = assert_regression(binary, "forward_gap_secondary_voice.xml")

    assert_contains(result.stdout, b"8ryy")
    assert_not_contains(result.stderr, b"Inconsistent rhythm analysis")


def test_terminal_forward_secondary_voice(binary: Path) -> None:
    result = assert_regression(binary, "terminal_forward_secondary_voice.xml")

    assert_stderr_not_matches(result.stderr, rb"Negative duration|Inconsistent rhythm analysis")
    assert_contains(result.stdout, b"4..C#\t8CC#")
    assert_contains(result.stdout, b".\t4.ryy")
    assert_contains(result.stdout, b"*v\t*v")


def test_late_voice_entry_during_rest(binary: Path) -> None:
    result = assert_regression(binary, "late_voice_entry_during_rest.xml")

    assert_not_contains(result.stderr, b"Inconsistent rhythm analysis")
    assert_contains(result.stdout, b"4r\t4G#\t8ee")


def test_note_split_at_layer_entry(binary: Path) -> None:
    result = assert_regression(binary, "note_split_at_layer_entry.xml")

    assert_stderr_not_matches(
        result.stderr,
        rb"Negative duration|Inconsistent rhythm analysis|Cannot deal with this slice addition case",
    )
    assert_contains(result.stdout, b"[4b")
    assert_contains(result.stdout, b"4b]\t4cc")


def test_late_voice_reentry_during_tied_note(binary: Path) -> None:
    result = assert_regression(binary, "late_voice_reentry_during_tied_note.xml")

    assert_stderr_not_matches(
        result.stderr,
        rb"Negative duration|Inconsistent rhythm analysis|Cannot deal with this slice addition case",
    )
    assert_contains(result.stdout, b"[4.e-")
    assert_contains(result.stdout, b"4.e-]")


def test_rounded_tuplet_compensating_forward(binary: Path) -> None:
    result = assert_regression(binary, "rounded_tuplet_compensating_forward.xml")

    assert_stderr_not_matches(
        result.stderr,
        rb"Negative duration|Inconsistent rhythm analysis|Cannot deal with this slice addition case",
    )
    assert_not_contains(result.stdout, b"ryy")
    assert_contains(result.stdout, b"14cL")


def test_dangling_x_after_transposition(binary: Path) -> None:
    result = assert_regression(binary, "dangling_x_after_transposition.xml")

    assert_contains(result.stdout, b"4enX")
    assert_contains(result.stdout, b"4g-X")
    assert_not_contains(result.stdout, b"4eX")


def test_zzz_hidden_measure_rest_collision(binary: Path) -> None:
    result = assert_regression(binary, "zzz_hidden_measure_rest_collision.xml")

    assert_not_contains(result.stdout, b".ZZZ")
    assert_not_contains(result.stdout, b"ryy@")
    assert_not_contains(result.stderr, b"Warning, replacing existing token")
    assert_contains(result.stdout, b"2.ryy")
    assert_contains(result.stdout, b"4r")
