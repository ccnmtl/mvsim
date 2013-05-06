from django.test import TestCase
from django.test.client import Client
from mvsim.main.models import CourseSection
from mvsim.main.models import Game


class SimpleTest(TestCase):
    def setUp(self):
        self.c = Client()

    def test_root(self):
        response = self.c.get("/")
        self.assertEquals(response.status_code, 302)

    def test_smoke(self):
        response = self.c.get("/smoketest/")
        print response
        self.assertEqual(response.status_code, 200)


class PlayGameTest(TestCase):
    """ the goal here is to get very basic coverage
    of the most important path through the app.

    User logs in, starts a new game, plays a turn,
    views history, deletes the game.

    not really checking any important functionality,
    but this test should at least catch any 500 errors
    popping up in that path """

    fixtures = ['test_course.json']

    def setUp(self):
        self.c = Client()

    def test_play(self):
        self.c.login(username='admin', password='admin')
        cs = CourseSection.objects.get(name="Default Section")
        response = self.c.get("/section/%d/games/" % cs.id)
        self.assertEqual(response.status_code, 200)

        s = cs.starting_states.all()[0]
        response = self.c.post("/section/%d/games/new/" % cs.id,
                               dict(starting_state_id=s.id),
                               follow=True)
        self.assertEqual(len(response.redirect_chain), 1)

        game_url = response.redirect_chain[0][0]
        print game_url
        assert game_url.startswith("http://testserver/games/")
        game_id = game_url.split("/")[4]
        g = Game.objects.get(id=game_id)

        # submit a turn, not setting any variables
        # so we don't expect a happy outcome
        response = self.c.post(
            "/games/%d/turn/" % g.id,
            dict()
        )
        self.assertEqual(response.status_code, 302)

        # check history stuff
        response = self.c.get("/games/%d/history/" % g.id)
        self.assertEqual(response.status_code, 200)

        response = self.c.get("/games/%d/game_over/" % g.id)
        self.assertEqual(response.status_code, 200)

        response = self.c.get("/games/%d/graph/" % g.id)
        self.assertEqual(response.status_code, 200)

        response = self.c.get("/games/%d/edit/" % g.id)
        self.assertEqual(response.status_code, 200)

        # clean up
        response = self.c.post("/games/%d/delete/" % g.id)
        self.assertEqual(response.status_code, 302)
