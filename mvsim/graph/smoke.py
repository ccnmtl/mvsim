from smoketest import SmokeTest
from django.conf import settings
import os


class GraphsDirectoryTest(SmokeTest):
    def setting_exists(self):
        self.assertIsNotNone(settings.MVSIM_GRAPH_OUTPUT_DIRECTORY)

    def test_exists(self):
        self.assertTrue(os.path.exists(settings.MVSIM_GRAPH_OUTPUT_DIRECTORY))
        self.assertTrue(os.path.isdir(settings.MVSIM_GRAPH_OUTPUT_DIRECTORY))
