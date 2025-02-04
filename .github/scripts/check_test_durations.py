import json
import sys

# Get report filename and threshold from command-line arguments
REPORT_FILE = sys.argv[1] if len(sys.argv) > 1 else "report.json"
THRESHOLD = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0

try:
    with open(REPORT_FILE) as f:
        data = json.load(f)
except FileNotFoundError:
    print(f"❌ Error: Report file '{REPORT_FILE}' not found.")
    sys.exit(1)
except json.JSONDecodeError:
    print(f"❌ Error: Failed to parse JSON in '{REPORT_FILE}'.")
    sys.exit(1)

slow_tests = [
    (t["nodeid"], t["call"]["duration"])
    for t in data.get("tests", [])
    if "call" in t and t["call"]["duration"] > THRESHOLD
]

if slow_tests:
    print(f"❌ The following tests exceeded the {THRESHOLD:.2f}s threshold:")
    for test, duration in slow_tests:
        print(f" - {test}: {duration:.2f}s")
    sys.exit(1)

print("✅ All tests ran within the acceptable time limit.")
