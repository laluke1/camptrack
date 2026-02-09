import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


def run_tests() -> int:
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests', pattern='test_*.py')
    test_runner = unittest.TextTestRunner(verbosity=2)
    test_result = test_runner.run(test_suite)
    return 0 if test_result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
