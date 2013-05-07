from django.test import TestCase
from mvsim.main.models import CourseSection, Game, Configuration
from mvsim.main.models import UserInput, State
from courseaffils.models import Course
from django.contrib.auth.models import Group, User


class CourseSectionTest(TestCase):
    def setUp(self):
        self.g = Group.objects.create(name="testgroup")
        self.fg = Group.objects.create(name="facultygroup")
        self.c = Course.objects.create(
            group=self.g, faculty_group=self.fg,
            title="test course")
        self.cs = CourseSection.objects.create(
            name="test course",
            course=self.c)

    def tearDown(self):
        self.cs.delete()
        self.c.delete()
        self.g.delete()
        self.fg.delete()

    def test_unicode(self):
        self.assertEquals(str(self.cs), "test course")

    def test_available_states(self):
        self.cs.ensure_default_starting_state()
        self.assertEquals(self.cs.available_states().count(), 0)

    def test_stats(self):
        r = list(self.cs.stats())
        self.assertEquals(len(r), 0)


class GameTest(TestCase):
    def setUp(self):
        self.g = Group.objects.create(name="testgroup")
        self.fg = Group.objects.create(name="facultygroup")
        self.c = Course.objects.create(
            group=self.g, faculty_group=self.fg,
            title="test course")
        self.cs = CourseSection.objects.create(
            name="test course",
            course=self.c)
        self.u = User.objects.create(username="testuser")
        self.conf = Configuration.objects.create(
            name="testconfig"
        )
        self.ui = UserInput.objects.create()
        self.game = Game.objects.create(
            user=self.u,
            configuration=self.conf,
            user_input=self.ui,
            course=self.c,
        )

    def tearDown(self):
        self.cs.delete()
        self.c.delete()
        self.g.delete()
        self.fg.delete()
        self.u.delete()
        self.conf.delete()

    def test_unicode(self):
        self.assertEquals(
            str(self.game),
            "testuser - in course test course [1]")
        self.game.name = "testgame"
        self.game.save()
        self.assertEquals(
            str(self.game),
            "testgame")

    def test_delete_url(self):
        self.assertEquals(
            self.game.delete_url(),
            "/games/%d/delete/" % self.game.id)

    def test_game_over_url(self):
        self.assertEquals(
            self.game.game_over_url(),
            "/games/%d/game_over/" % self.game.id)

    def test_graph_url(self):
        self.assertEquals(
            self.game.graph_url(),
            "/games/%d/graph/" % self.game.id)

    def test_course_section(self):
        s = self.game.course_section(self.u)


class StateTest(TestCase):
    def setUp(self):
        self.g = Group.objects.create(name="testgroup")
        self.fg = Group.objects.create(name="facultygroup")
        self.c = Course.objects.create(
            group=self.g, faculty_group=self.fg,
            title="test course")
        self.cs = CourseSection.objects.create(
            name="test course",
            course=self.c)
        self.u = User.objects.create(username="testuser")
        self.conf = Configuration.objects.create(
            name="testconfig"
        )
        self.ui = UserInput.objects.create()
        self.game = Game.objects.create(
            user=self.u,
            configuration=self.conf,
            user_input=self.ui,
            course=self.c,
        )
        self.state = State.objects.create(
            name="teststate",
            game=self.game,
            state='{"coefficients": {"foo": 1}, "variables": {"bar": 1}}',
        )
        self.blank_game = Game.objects.create(
            user=self.u,
            configuration=self.conf,
            user_input=self.ui,
            course=self.c,
        )

    def tearDown(self):
        self.state.delete()
        self.cs.delete()
        self.c.delete()
        self.g.delete()
        self.fg.delete()
        self.u.delete()
        self.conf.delete()

    def test_unicode(self):
        self.assertEquals(
            str(self.state),
            "teststate")
        self.state.name = ""
        self.state.save()
        self.assertEquals(
            str(self.state),
            "testuser - in course test course [1]: turn 1"
        )

    def test_game_init(self):
        self.blank_game.init(self.state)

    def test_game_init_notblank(self):
        with self.assertRaises(RuntimeError):
            self.game.init(self.state)
