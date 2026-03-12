import tempfile
import unittest
from pathlib import Path

import tools


class ExecuteTerminalTests(unittest.TestCase):
    def setUp(self) -> None:
        self._original_cwd = tools._CURRENT_WORKDIR
        tools._CURRENT_WORKDIR = Path.cwd()

    def tearDown(self) -> None:
        tools._CURRENT_WORKDIR = self._original_cwd

    def test_rejects_non_allowed_command(self) -> None:
        result = tools.execute_terminal("ls -la")
        self.assertEqual(result["returncode"], -1)
        self.assertIn("Command not allowed", result["stderr"])

    def test_cd_persists_for_next_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            cd_result = tools.execute_terminal(f"cd {tmp_dir}")
            self.assertEqual(cd_result["returncode"], 0)

            cwd_result = tools.execute_terminal('python3 -c "import os; print(os.getcwd())"')
            self.assertEqual(cwd_result["returncode"], 0)
            observed_cwd = Path(cwd_result["stdout"].strip()).resolve()
            self.assertEqual(observed_cwd, Path(tmp_dir).resolve())

    def test_shell_injection_sequence_not_executed(self) -> None:
        result = tools.execute_terminal('python3 -c "print(1)"; python3 -c "print(2)"')
        self.assertEqual(result["returncode"], 0)
        self.assertIn("1", result["stdout"])
        self.assertNotIn("2", result["stdout"])


if __name__ == "__main__":
    unittest.main()
