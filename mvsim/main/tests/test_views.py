from django.test import TestCase
from django.test.client import Client
from mvsim.main.models import CourseSection
from mvsim.main.models import Game
from django.contrib.auth.models import User


class SimpleTest(TestCase):
    def setUp(self):
        self.c = Client()

    def test_root(self):
        response = self.c.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'You are not in any course sections.')
        self.assertContains(response, 'Log in')

    def test_smoke(self):
        self.c.get("/smoketest/")


class LoggedInTest(TestCase):
    def setUp(self):
        self.c = Client()
        self.u = User.objects.create(username="testuser")
        self.u.set_password("test")
        self.u.save()
        self.c.login(username="testuser", password="test")

    def tearDown(self):
        self.u.delete()

    def test_root(self):
        response = self.c.get("/")
        self.assertEqual(response.status_code, 200)

    def test_course_auto_creation(self):
        # first one should auto-create a course
        response = self.c.get("/")
        self.assertContains(response, "Default Section")
        # second one it should already be created
        response = self.c.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Default Section")


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
        u = User.objects.get(username='admin')
        u.set_password('admin')
        u.save()
        self.c.login(username='admin', password='admin')

    def test_play(self):
        cs = CourseSection.objects.get(name="Default Section")
        response = self.c.get("/section/%d/games/" % cs.id)
        self.assertEqual(response.status_code, 200)

        s = cs.starting_states.all()[0]
        response = self.c.post("/section/%d/games/new/" % cs.id,
                               dict(starting_state_id=s.id),
                               follow=True)
        self.assertEqual(len(response.redirect_chain), 1)

        game_url = response.redirect_chain[0][0]
        assert game_url.startswith("/games/")
        game_id = game_url.split("/")[2]
        g = Game.objects.get(id=game_id)

        # submit a turn, not setting any variables
        # so we don't expect a happy outcome
        response = self.c.post(
            "/games/%d/turn/" % g.id,
            {'effort-Kodjo': '12',
             'effort-Fatou': '12',
             'effort_farming': '15',
             'effort_fishing': '0',
             'effort_fuel_wood': '3',
             'effort_water': '6',
             'effort_small_business': '0',
             'maize': '4',
             'cotton': '0',
             }
        )
        self.assertEqual(response.status_code, 302)

        response = self.c.get("/games/%d/" % g.id)
        self.assertEqual(response.status_code, 200)

        # check history stuff
        response = self.c.get("/games/%d/history/" % g.id)
        self.assertEqual(response.status_code, 200)

        response = self.c.get("/games/%d/turn/1/" % g.id)
        self.assertEqual(response.status_code, 200)

        response = self.c.get("/games/%d/turn/2/" % g.id)
        self.assertEqual(response.status_code, 200)

        response = self.c.get("/games/%d/game_over/" % g.id)
        self.assertEqual(response.status_code, 302)

        response = self.c.get("/games/%d/graph/" % g.id)
        self.assertEqual(response.status_code, 200)

        response = self.c.get("/games/%d/edit/" % g.id)
        self.assertEqual(response.status_code, 200)

        # clean up
        response = self.c.post("/games/%d/delete/" % g.id)
        self.assertEqual(response.status_code, 302)

    def test_play_suicide(self):
        """ play a turn that ought to end the game """
        cs = CourseSection.objects.get(name="Default Section")
        response = self.c.get("/section/%d/games/" % cs.id)
        self.assertEqual(response.status_code, 200)

        s = cs.starting_states.all()[0]
        response = self.c.post("/section/%d/games/new/" % cs.id,
                               dict(starting_state_id=s.id),
                               follow=True)
        self.assertEqual(len(response.redirect_chain), 1)

        game_url = response.redirect_chain[0][0]
        assert game_url.startswith("/games/")
        game_id = game_url.split("/")[2]
        g = Game.objects.get(id=game_id)

        # submit a turn, not setting any variables
        # so we don't expect a happy outcome
        response = self.c.post(
            "/games/%d/turn/" % g.id,
            {}
        )
        self.assertEqual(response.status_code, 302)

        response = self.c.get("/games/%d/game_over/" % g.id)
        self.assertEqual(response.status_code, 200)

        # clean up
        response = self.c.post("/games/%d/delete/" % g.id)
        self.assertEqual(response.status_code, 302)

    def test_game_auth(self):
        """ play a turn to get a game started,
        then try to access it as a different user """
        cs = CourseSection.objects.get(name="Default Section")
        response = self.c.get("/section/%d/games/" % cs.id)
        self.assertEqual(response.status_code, 200)

        s = cs.starting_states.all()[0]
        response = self.c.post("/section/%d/games/new/" % cs.id,
                               dict(starting_state_id=s.id),
                               follow=True)
        self.assertEqual(len(response.redirect_chain), 1)

        game_url = response.redirect_chain[0][0]
        assert game_url.startswith("/games/")
        game_id = game_url.split("/")[2]
        g = Game.objects.get(id=game_id)

        # submit a turn, not setting any variables
        # so we don't expect a happy outcome
        response = self.c.post(
            "/games/%d/turn/" % g.id,
            {'effort-Kodjo': '12',
             'effort-Fatou': '12',
             'effort_farming': '15',
             'effort_fishing': '0',
             'effort_fuel_wood': '3',
             'effort_water': '6',
             'effort_small_business': '0',
             'maize': '4',
             'cotton': '0',
             }
        )
        self.assertEqual(response.status_code, 302)

        u2 = User.objects.create(username="testuser2")
        u2.set_password('test')
        u2.save()
        self.c.login(username="testuser2", password="test")

        # make sure we are denied access to everything
        response = self.c.get("/games/%d/" % g.id)
        self.assertEqual(response.status_code, 403)

        response = self.c.post(
            "/games/%d/turn/" % g.id,
            {'effort-Kodjo': '12',
             'effort-Fatou': '12',
             'effort_farming': '15',
             'effort_fishing': '0',
             'effort_fuel_wood': '3',
             'effort_water': '6',
             'effort_small_business': '0',
             'maize': '4',
             'cotton': '0',
             }
        )
        self.assertEqual(response.status_code, 403)

        response = self.c.get("/games/%d/history/" % g.id)
        self.assertEqual(response.status_code, 403)

        response = self.c.get("/games/%d/turn/1/" % g.id)
        self.assertEqual(response.status_code, 403)

        response = self.c.get("/games/%d/turn/2/" % g.id)
        self.assertEqual(response.status_code, 403)

        response = self.c.get("/games/%d/game_over/" % g.id)
        self.assertEqual(response.status_code, 403)

        response = self.c.get("/games/%d/graph/" % g.id)
        self.assertEqual(response.status_code, 403)

        response = self.c.get("/games/%d/edit/" % g.id)
        self.assertEqual(response.status_code, 403)

        response = self.c.post("/games/%d/delete/" % g.id)
        self.assertEqual(response.status_code, 403)

        u2.delete()
