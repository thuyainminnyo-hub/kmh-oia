"""Fail closed when any required KMH OIA CI prerequisite did not succeed."""

import os
import sys


def main() -> int:
    required = {
        "tests": os.environ.get("TESTS_RESULT", ""),
        "performance-evidence": os.environ.get("PERFORMANCE_RESULT", ""),
        "repository-validation": os.environ.get("REPOSITORY_RESULT", ""),
    }
    failed = {name: result for name, result in required.items() if result != "success"}
    if failed:
        print(f"Required prerequisite jobs did not succeed: {failed}", file=sys.stderr)
        return 1
    print("All required prerequisite jobs succeeded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
