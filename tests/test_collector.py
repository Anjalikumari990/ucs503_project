"""Collector setup checks with a stub keyboard backend; never starts a listener."""
import contextlib
import importlib.util
import io
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load_collector():
    fake_keyboard = types.SimpleNamespace(KeyCode=type('KeyCode', (), {}))
    spec = importlib.util.spec_from_file_location('collector_under_test', ROOT / 'code/collectors/keyboard_logger.py')
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {'pynput': types.SimpleNamespace(keyboard=fake_keyboard)}):
        spec.loader.exec_module(module)
    return module


class CollectorTests(unittest.TestCase):
    def test_data_location_is_independent_of_working_directory(self):
        module = load_collector()
        self.assertEqual(module.DATA_DIR, ROOT / 'code/data')
        self.assertEqual(Path(module.SECRET_FILE), ROOT / 'code/data/key_hash_secret.bin')

    def test_existing_session_is_preserved(self):
        module = load_collector()
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory)
            output = data / 'raw/own/U02/S01/keyboard.csv'
            output.parent.mkdir(parents=True)
            output.write_text('existing recording\n')
            with patch.object(module, 'DATA_DIR', data), patch.object(sys, 'argv', ['collector', '--user', 'U02', '--session', 'S01']):
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
                    module.main()
            self.assertEqual(raised.exception.code, 2)
            self.assertEqual(output.read_text(), 'existing recording\n')
            self.assertFalse((data / 'key_hash_secret.bin').exists())

    def test_identifiers_cannot_escape_data_directory(self):
        module = load_collector()
        with patch.object(sys, 'argv', ['collector', '--user', '../outside', '--session', 'S01']):
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
                module.main()
        self.assertEqual(raised.exception.code, 2)

    def test_secret_is_reused_and_hashes_do_not_store_key_labels(self):
        module = load_collector()
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory)
            with patch.object(module, 'DATA_DIR', data), patch.object(module, 'SECRET_FILE', data / 'key_hash_secret.bin'):
                secret = module.get_or_create_secret()
                self.assertEqual(len(secret), 32)
                self.assertEqual(secret, module.get_or_create_secret())
                digest = module.get_key_identifier('a', secret)
                self.assertRegex(digest, r'^[0-9a-f]{64}$')
                self.assertEqual(digest, module.get_key_identifier('a', secret))
                self.assertNotEqual(digest, module.get_key_identifier('b', secret))


if __name__ == '__main__':
    unittest.main()
