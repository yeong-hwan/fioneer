import unittest
import sys

def run_tests():
    """Run all tests with verbose output"""
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests', pattern='test_*.py')
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    sys.exit(not result.wasSuccessful())

def run_tests_quiet():
    """Run all tests with minimal output"""
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests', pattern='test_*.py')
    runner = unittest.TextTestRunner(verbosity=0)
    result = runner.run(test_suite)
    sys.exit(not result.wasSuccessful())

if __name__ == '__main__':
    run_tests() 