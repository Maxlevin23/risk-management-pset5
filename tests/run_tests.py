"""Run every test without pytest:  python tests/run_tests.py

pytest gives nicer output (``python -m pytest``); this runner needs nothing
beyond the standard library, so the tests can be checked on any machine.
"""

import importlib
import sys
import traceback
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TEST_DIR))

import conftest  # noqa: E402,F401  (puts src/ and the project root on the path)


def main():
    """Import each ``test_*.py`` module, call each ``test_*`` function, report."""
    passed, failed = 0, 0
    for path in sorted(TEST_DIR.glob("test_*.py")):
        module = importlib.import_module(path.stem)
        print(path.name)
        for name in sorted(vars(module)):
            if not name.startswith("test_"):
                continue
            try:
                getattr(module, name)()
                passed += 1
                print(f"  ok    {name}")
            except Exception:
                failed += 1
                print(f"  FAIL  {name}")
                traceback.print_exc()
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
