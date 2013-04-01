from django.test import TestCase
from courseaffils.models import Course
from mvsim.main.models import CourseSection, State


class AdminCourseTest(TestCase):
    fixtures = ['test_course.json']

    def test_default_course_setup(self):
        # When a course is created, it automatically gets a section
        # and is associated with the default state
        course = Course.objects.get(id=1)
        self.assertEquals(len(course.coursesection_set.all()), 1)

        section = CourseSection.objects.get(id=1)
        self.assertEquals(section.name, 'Default Section')

        self.assertEquals(len(section.starting_states.all()), 1)
        state = section.starting_states.get(id=1)
        self.assertEquals('Default Starting State', state.name)

        state = State.objects.get(id=1)
        self.assertEquals(len(state.coursesection_set.all()), 1)
