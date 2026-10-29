import contextlib
import importlib.util
import io
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

# Resolve base project directory dynamically
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = CURRENT_DIR.parent if CURRENT_DIR.parent.name != "code" else CURRENT_DIR.parents[1]


def load_collector():
    fake_keyboard = types.SimpleNamespace(KeyCode=type("KeyCode", (), {}))
    
    # Locate keyboard_logger whether in code/collectors or root collectors
    collector_path = PROJECT_DIR / "code/collectors/keyboard_logger.py"
    if not collector_path.exists():
        collector_path = PROJECT_DIR / "collectors/keyboard_logger.py"

    spec = importlib.util.spec_from_file_location("collector_under_test", collector_path)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {"pynput": types.SimpleNamespace(keyboard=fake_keyboard)}):
        spec.loader.exec_module(module)
    return module


class CollectorTests(unittest.TestCase):
    def test_data_location_is_independent_of_working_directory(self):
        module = load_collector()
        expected_data = PROJECT_DIR / "code/data" if (PROJECT_DIR / "code").is_dir() else PROJECT_DIR / "data"
        self.assertEqual(module.DATA_DIR, expected_data)
        self.assertEqual(Path(module.SECRET_FILE), expected_data / "key_hash_secret.bin")

    def test_existing_session_is_preserved(self):
        module = load_collector()
        with tempfile.TemporaryDirectory() as temp_dir:
            data = Path(temp_dir)
            output = data / "raw/own/U02/S01/keyboard.csv"
            output.parent.mkdir(parents=True)
            output.write_text("existing recording\n")

            with patch.object(module, "DATA_DIR", data), patch.object(sys, "argv", ["collector", "--user", "U02", "--session", "S01"]):
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
                    module.main()
            self.assertEqual(raised.exception.code, 2)
            self.assertEqual(output.read_text(), "existing recording\n")
            self.assertFalse((data / "key_hash_secret.bin").exists())

    def test_identifiers_cannot_escape_data_directory(self):
        module = load_collector()
        with patch.object(sys, "argv", ["collector", "--user", "../outside", "--session", "S01"]):
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
                module.main()
        self.assertEqual(raised.exception.code, 2)

    def test_secret_is_reused_and_hashes_do_not_store_key_labels(self):
        module = load_collector()
        with tempfile.TemporaryDirectory() as temp_dir:
            data = Path(temp_dir)
            with patch.object(module, "DATA_DIR", data), patch.object(module, "SECRET_FILE", data / "key_hash_secret.bin"):
                secret = module.get_or_create_secret()
                self.assertEqual(len(secret), 32)
                self.assertEqual(secret, module.get_or_create_secret())
                digest = module.get_key_identifier("a", secret)
                self.assertRegex(digest, r"^[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
