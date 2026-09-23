import unittest
import sys
import os

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def run_all_tests():
    print("=" * 65)
    print("  RUNNING AI EQUITY INTELLIGENCE TEST SUITE")
    print("=" * 65)
    
    loader = unittest.TestLoader()
    start_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../tests"))
    suite = loader.discover(start_dir, pattern="test_*.py")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 65)
    print(f"  Tests Run: {result.testsRun}")
    print(f"  Failures:  {len(result.failures)}")
    print(f"  Errors:    {len(result.errors)}")
    print("=" * 65)
    
    if result.wasSuccessful():
        print(">>> ALL TESTS PASSED SUCCESSFULLY! <<<")
        sys.exit(0)
    else:
        print(">>> TEST SUITE ENCOUNTERED FAILURES <<<")
        sys.exit(1)

if __name__ == "__main__":
    run_all_tests()
