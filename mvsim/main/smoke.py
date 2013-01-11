from smoketest import SmokeTest
from models import Variable


class DBConnectivity(SmokeTest):
    def test_retrieve(self):
        cnt = Variable.objects.all().count()
        self.assertTrue(cnt > 0)
