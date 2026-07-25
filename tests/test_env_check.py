# tests/test_env_check.py
import os
import unittest

from config.env_check import validate_environment


class TestEnvCheck(unittest.TestCase):

    def setUp(self):
        self._saved = {k: os.environ.get(k) for k in ('APP_ENV', 'SECRET_KEY')}

    def tearDown(self):
        for key, value in self._saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_production_without_secret_key_raises(self):
        os.environ['APP_ENV'] = 'production'
        os.environ.pop('SECRET_KEY', None)
        with self.assertRaises(RuntimeError):
            validate_environment()

    def test_production_with_secret_key_does_not_raise(self):
        os.environ['APP_ENV'] = 'production'
        os.environ['SECRET_KEY'] = 'a-real-production-secret'
        validate_environment()  # should not raise

    def test_development_without_secret_key_does_not_raise(self):
        os.environ['APP_ENV'] = 'development'
        os.environ.pop('SECRET_KEY', None)
        validate_environment()  # dev fallback is allowed


if __name__ == '__main__':
    unittest.main()
