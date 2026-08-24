import sys
import unittest

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

from tests.test_architecture_verification import TestArchitectureVerification

suite = unittest.TestLoader().loadTestsFromTestCase(TestArchitectureVerification)
runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)

if result.wasSuccessful():
    print("\nALL ARCHITECTURE VERIFICATION TESTS PASSED SUCCESSFULLY!")
    sys.exit(0)
else:
    print("\nSOME TESTS FAILED.")
    sys.exit(1)
