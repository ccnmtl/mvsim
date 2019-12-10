from smoketest import SmokeTest

from mvsim.main.models import Variable


class DBConnectivity(SmokeTest):
    def test_retrieve(self):
        cnt = Variable.objects.all().count()
        self.assertTrue(cnt > 0)
