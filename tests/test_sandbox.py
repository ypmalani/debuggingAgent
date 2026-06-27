import tempfile
import unittest

from sandbox import run_tests


class RunTestsSandboxCase(unittest.TestCase):
    def test_returns_captured_output_for_successful_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_tests(
                temp_dir,
                "python3 -c \"print('sandbox-ok')\"",
                timeout=5,
            )

        self.assertTrue(result["success"])
        self.assertIn("sandbox-ok", result["stdout"])
        self.assertEqual("", result["stderr"])

    def test_returns_timeout_error_for_slow_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_tests(
                temp_dir,
                "python3 -c \"import time; time.sleep(2)\"",
                timeout=1,
            )

        self.assertFalse(result["success"])
        self.assertIn("Timeout Error", result["stderr"])


if __name__ == "__main__":
    unittest.main()
