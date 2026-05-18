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

echo "----------------------------------------"
echo "Results: $PASSED passed, $FAILED failed"

if [[ $FAILED -gt 0 ]]; then
    exit 1
fi
