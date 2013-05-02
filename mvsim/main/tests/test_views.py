from django.test import TestCase
from django.test.client import Client


class SimpleTest(TestCase):
    def setUp(self):
        self.c = Client()

    def test_root(self):
        response = self.c.get("/")
        self.assertEquals(response.status_code, 302)

    def test_smoke(self):
        response = self.c.get("/smoketest/")
        self.assertEqual(response.status_code, 200)
