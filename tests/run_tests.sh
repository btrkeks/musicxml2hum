#!/bin/bash
# Test script for musicxml2hum
# Usage: ./tests/run_tests.sh [binary]

BINARY="${1:-./bin/musicxml2hum}"
TESTDIR="$(dirname "$0")"
PASSED=0
FAILED=0

if [[ ! -x "$BINARY" ]]; then
    echo "Error: Binary not found or not executable: $BINARY"
    echo "Run 'make release' first."
    exit 1
fi

echo "Testing with: $BINARY"
echo "----------------------------------------"

for xmlfile in "$TESTDIR"/*.xml; do
    name=$(basename "$xmlfile" .xml)
    if "$BINARY" "$xmlfile" > /dev/null 2>&1; then
        echo "PASS: $name"
        ((PASSED++))
    else
        echo "FAIL: $name"
        ((FAILED++))
    fi
done

echo "Checking regression: leading equals lyrics"
output="$("$BINARY" "$TESTDIR/leading_equals_lyrics.xml")"
if printf '%s\n' "$output" | grep -F $'4g\t\\=A-\tHear' >/dev/null &&
   printf '%s\n' "$output" | grep -F $'4a\t\\=cevs\t.' >/dev/null &&
   printf '%s\n' "$output" | grep -F $'4b\t\\= E\t.' >/dev/null &&
   printf '%s\n' "$output" | grep -F $'4cc\t\\= E\t.' >/dev/null &&
   ! printf '%s\n' "$output" | grep -E $'^[^=\t][^\t]*\t=' >/dev/null; then
    echo "PASS: leading_equals_lyrics"
    ((PASSED++))
else
    echo "FAIL: leading_equals_lyrics"
    printf '%s\n' "$output"
    ((FAILED++))
fi

echo "Checking regression: hidden extra voice rest spine"
tmpout="$(mktemp)"
tmperr="$(mktemp)"
if "$BINARY" "$TESTDIR/hidden_extra_voice_rest_spine.xml" >"$tmpout" 2>"$tmperr" &&
   ! grep -E 'Expected [0-9]+ fields|spine [0-9]+ is not terminated' "$tmperr" >/dev/null &&
   grep -F '*^' "$tmpout" >/dev/null &&
   grep -F '*v' "$tmpout" >/dev/null; then
    echo "PASS: hidden_extra_voice_rest_spine"
    ((PASSED++))
else
    echo "FAIL: hidden_extra_voice_rest_spine"
    cat "$tmperr"
    cat "$tmpout"
    ((FAILED++))
fi
rm -f "$tmpout" "$tmperr"

echo "Checking regression: secondary voice forward gap"
tmpout="$(mktemp)"
tmperr="$(mktemp)"
if "$BINARY" "$TESTDIR/forward_gap_secondary_voice.xml" >"$tmpout" 2>"$tmperr" &&
   grep -F '8ryy' "$tmpout" >/dev/null &&
   ! grep -F 'Inconsistent rhythm analysis' "$tmperr" >/dev/null; then
    echo "PASS: forward_gap_secondary_voice"
    ((PASSED++))
else
    echo "FAIL: forward_gap_secondary_voice"
    cat "$tmperr"
    cat "$tmpout"
    ((FAILED++))
fi
rm -f "$tmpout" "$tmperr"

echo "Checking regression: late voice entry during rest"
tmpout="$(mktemp)"
tmperr="$(mktemp)"
if "$BINARY" "$TESTDIR/late_voice_entry_during_rest.xml" >"$tmpout" 2>"$tmperr" &&
   ! grep -F 'Inconsistent rhythm analysis' "$tmperr" >/dev/null &&
   grep -F $'4r\t4G#\t8ee' "$tmpout" >/dev/null; then
    echo "PASS: late_voice_entry_during_rest"
    ((PASSED++))
else
    echo "FAIL: late_voice_entry_during_rest"
    cat "$tmperr"
    cat "$tmpout"
    ((FAILED++))
fi
rm -f "$tmpout" "$tmperr"

echo "Checking regression: dangling X after transposition"
tmpout="$(mktemp)"
tmperr="$(mktemp)"
if "$BINARY" "$TESTDIR/dangling_x_after_transposition.xml" >"$tmpout" 2>"$tmperr" &&
   grep -F '4enX' "$tmpout" >/dev/null &&
   grep -F '4g-X' "$tmpout" >/dev/null &&
   ! grep -F '4eX' "$tmpout" >/dev/null; then
    echo "PASS: dangling_x_after_transposition"
    ((PASSED++))
else
    echo "FAIL: dangling_x_after_transposition"
    cat "$tmperr"
    cat "$tmpout"
    ((FAILED++))
fi
rm -f "$tmpout" "$tmperr"

echo "Checking regression: ZZZ hidden measure rest collision"
tmpout="$(mktemp)"
tmperr="$(mktemp)"
if "$BINARY" "$TESTDIR/zzz_hidden_measure_rest_collision.xml" >"$tmpout" 2>"$tmperr" &&
   ! grep -F '.ZZZ' "$tmpout" >/dev/null &&
   ! grep -F 'ryy@' "$tmpout" >/dev/null &&
   ! grep -F 'Warning, replacing existing token' "$tmperr" >/dev/null &&
   grep -F '2.ryy' "$tmpout" >/dev/null &&
   grep -F '4r' "$tmpout" >/dev/null; then
    echo "PASS: zzz_hidden_measure_rest_collision"
    ((PASSED++))
else
    echo "FAIL: zzz_hidden_measure_rest_collision"
    cat "$tmperr"
    cat "$tmpout"
    ((FAILED++))
fi
rm -f "$tmpout" "$tmperr"

echo "----------------------------------------"
echo "Results: $PASSED passed, $FAILED failed"

if [[ $FAILED -gt 0 ]]; then
    exit 1
fi
