from django.test import TestCase
from mvsim.main.models import CourseSection, Game, Configuration
from mvsim.main.models import UserInput
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
