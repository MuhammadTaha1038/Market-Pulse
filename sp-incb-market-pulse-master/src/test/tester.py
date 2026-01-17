import sys
import os
import unittest
from fastapi.testclient import TestClient
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(2, os.path.abspath(os.path.join(os.path.dirname(__file__), '../main')))
from main.handler import app

PREFIX = os.environ.get('BASE_PATH', "")
client = TestClient(app)

class DefaultTestCase(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health(self):
        response = self.client.get(PREFIX + "/health")
        self.assertTrue(response.status_code == 200)

    def test_version(self):
        response = self.client.get(PREFIX + "/version")
        self.assertTrue(response.status_code == 200)

if __name__ == '__main__':
    unittest.main()
