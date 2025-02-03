import json
import sys

THRESHOLD = 1.0  # seconds

with open("report.json") as f:
    data = json.load(f)

slow_tests = [
    (t["nodeid"], t["call"]["duration"])
    for t in data["tests"]
    if "call" in t and t["call"]["duration"] > THRESHOLD
]

if slow_tests:
    print("❌ The following tests exceeded the 1s threshold:")
    for test, duration in slow_tests:
        print(f" - {test}: {duration:.2f}s")
    sys.exit(1)

print("✅ All tests ran within the acceptable time limit.")
