#!/usr/bin/env python
"""Run all VibeMatch tests and produce a summary report."""
import sys
import subprocess
import os

os.chdir(os.path.dirname(__file__) or '.')

test_files = [
    "tests/test_recommender.py",
    "tests/test_embedder.py",
    "tests/test_integration.py",
]

print("=" * 70)
print("VibeMatch Test Suite".center(70))
print("=" * 70)

total_passed = 0
total_failed = 0
results = []

for test_file in test_files:
    print(f"\n▶ Running {test_file}...")
    result = subprocess.run(
        [sys.executable, test_file],
        capture_output=True,
        text=True,
    )
    
    output = result.stdout + result.stderr
    print(output)
    
    # Parse pass/fail counts from output
    if "passed, 0 failed" in output:
        # Extract numbers
        import re
        match = re.search(r'(\d+) passed, (\d+) failed', output)
        if match:
            passed = int(match.group(1))
            failed = int(match.group(2))
            total_passed += passed
            total_failed += failed
            results.append((test_file, passed, failed))

print("\n" + "=" * 70)
print("Summary".center(70))
print("=" * 70)

for test_file, passed, failed in results:
    status = "✓ PASS" if failed == 0 else "✗ FAIL"
    print(f"{status} | {test_file}: {passed} passed, {failed} failed")

print("-" * 70)
print(f"Total: {total_passed} passed, {total_failed} failed")

if total_failed == 0:
    print("\n✓ All tests passed! System is reliable.".center(70))
else:
    print(f"\n✗ {total_failed} test(s) failed. Review above.".center(70))

print("=" * 70)

sys.exit(0 if total_failed == 0 else 1)
