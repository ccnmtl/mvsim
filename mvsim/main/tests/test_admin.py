from __future__ import unicode_literals

from courseaffils.models import Course
from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from mvsim.main.models import CourseSection, State


class AdminCourseTest(TestCase):
    fixtures = ['test_course.json']

    def test_default_course_setup(self):
        # When a course is created, it automatically gets a section
        # and is associated with the default state
        course = Course.objects.get(id=1)
        self.assertEqual(len(course.coursesection_set.all()), 1)

        section = CourseSection.objects.get(id=1)
        self.assertEqual(section.name, 'Default Section')

        self.assertEqual(len(section.starting_states.all()), 1)
        state = section.starting_states.get(id=1)
        self.assertEqual('Default Starting State', state.name)

        state = State.objects.get(id=1)
        self.assertEqual(state.visible, True)
        self.assertEqual(len(state.coursesection_set.all()), 1)

    def test_edit_state_access(self):
        client = Client()
        u = User.objects.get(username='test_instructor')
        u.set_password('test')
        u.save()

        self.assertTrue(
            client.login(username='test_instructor', password='test'))

        response = client.get("/state/1/")
        self.assertEqual(response.status_code, 403)
        response = client.post("/state/1/edit/")
        self.assertEqual(response.status_code, 403)
        response = client.post("/state/1/clone/")
        self.assertEqual(response.status_code, 403)

        u = User.objects.get(username='test_student_one')
        u.set_password('test')
        u.save()

        self.assertTrue(
            client.login(username='test_student_one', password='test'))
        response = client.get("/state/1/")
        self.assertEqual(response.status_code, 403)
        response = client.post("/state/1/edit/")
        self.assertEqual(response.status_code, 403)
        response = client.post("/state/1/clone/")
        self.assertEqual(response.status_code, 403)

    def test_edit_state_visibility(self):
        client = Client()
        u = User.objects.get(username='admin')
        u.set_password('admin')
        u.save()
        self.assertTrue(
            client.login(username='admin', password='admin'))

        response = client.get("/state/1/")
        self.assertTemplateUsed(response, "admin/view_state.html")

        state = State.objects.get(id=1)
        self.assertEqual(state.visible, True)
        self.assertEqual(len(state.coursesection_set.all()), 1)

        client.post("/state/1/edit/", {'visible': ['True'],
                                       'associated_sections': ['1']})
        state = State.objects.get(id=1)
        self.assertEqual(state.visible, True)

        client.post("/state/1/edit/", {'visible': ['False'],
                                       'associated_sections': ['1']})
        state = State.objects.get(id=1)
        self.assertEqual(state.visible, False)

        client.post("/state/1/edit/", {'visible': ['False'],
                                       'associated_sections': ['1']})
        state = State.objects.get(id=1)
        self.assertEqual(state.visible, False)

        client.post("/state/1/edit/", {'visible': "True",
                                       'associated_sections': ['1']})
        state = State.objects.get(id=1)
        self.assertEqual(state.visible, True)
        self.assertEqual(len(state.coursesection_set.all()), 1)

    def test_edit_state_sections(self):
        client = Client()
        u = User.objects.get(username='admin')
        u.set_password('admin')
        u.save()

        self.assertTrue(
            client.login(username='admin', password='admin'))

        response = client.get("/state/1/")
        self.assertTemplateUsed(response, "admin/view_state.html")

        state = State.objects.get(id=1)
        self.assertEqual(state.visible, True)
        self.assertEqual(len(state.coursesection_set.all()), 1)
        self.assertEqual(state.coursesection_set.all()[0].name,
                         "Default Section")

        client.post("/state/1/edit/", {'associated_sections': ['1']})
        self.assertEqual(len(state.coursesection_set.all()), 1)
        self.assertEqual(state.coursesection_set.all()[0].name,
                         "Default Section")

        client.post("/state/1/edit/", {})
        state = State.objects.get(id=1)
        self.assertEqual(len(state.coursesection_set.all()), 0)

        client.post("/state/1/edit/", {'associated_sections': []})
        state = State.objects.get(id=1)
        self.assertEqual(len(state.coursesection_set.all()), 0)

        client.post("/state/1/edit/", {'associated_sections': ['1']})
        state = State.objects.get(id=1)
        self.assertEqual(len(state.coursesection_set.all()), 1)
        self.assertEqual(state.coursesection_set.all()[0].name,
                         "Default Section")

        state = State.objects.get(id=1)
        self.assertEqual(state.visible, True)

    def test_clone_state(self):
        self.assertEqual(len(State.objects.all()), 2)
        starting_states = CourseSection.objects.get(id=1).starting_states.all()
        self.assertEqual(len(starting_states), 1)

        client = Client()
        u = User.objects.get(username='admin')
        u.set_password('admin')
        u.save()

        self.assertTrue(
            client.login(username='admin', password='admin'))

        response = client.get("/state/1/")
        self.assertTemplateUsed(response, "admin/view_state.html")

        client.post("/state/1/clone/",
                    {'visible': ['False'],
                     'associated_sections': ['1'],
                     'state_name': ['New State']})

        self.assertTemplateUsed(response, "admin/view_state.html")
        self.assertEqual(len(State.objects.all()), 3)
        new_state = State.objects.get(name="New State")
        self.assertFalse(new_state.visible)
        self.assertEqual(len(new_state.coursesection_set.all()), 1)
        self.assertEqual(new_state.coursesection_set.all()[0].name,
                         "Default Section")
        starting_states = CourseSection.objects.get(id=1).starting_states.all()
        self.assertEqual(len(starting_states), 2)
        self.assertEqual(starting_states[1], new_state)

        client.post("/state/1/clone/",
                    {'visible': ['True'],
                     'state_name': ['Another New State']})

        self.assertTemplateUsed(response, "admin/view_state.html")
        self.assertEqual(len(State.objects.all()), 4)
        new_state = State.objects.get(name="Another New State")
        self.assertTrue(new_state.visible)
        self.assertEqual(len(new_state.coursesection_set.all()), 0)

    def test_edit_section_states(self):
        client = Client()
        u = User.objects.get(username='admin')
        u.set_password('admin')
        u.save()

        self.assertTrue(
            client.login(username='admin', password='admin'))

        section = CourseSection.objects.get(id=1)
        self.assertEqual(section.name, "Default Section")
        self.assertEqual(section.starting_states.count(), 1)

        client.post("/course_sections/1/associate_state/",
                    {'associated_states': ['1']})
        self.assertEqual(section.starting_states.count(), 1)
        self.assertEqual(section.starting_states.all()[0].name,
                         "Default Starting State")

        client.post("/course_sections/1/associate_state/",
                    {'associated_states': []})
        self.assertEqual(section.starting_states.count(), 0)

        client.post("/course_sections/1/associate_state/",
                    {'associated_states': ['1']})
        self.assertEqual(section.starting_states.count(), 1)
        self.assertEqual(section.starting_states.all()[0].name,
                         "Default Starting State")

        client.post("/course_sections/1/associate_state/", {})
        self.assertEqual(section.starting_states.count(), 0)

        client.post("/course_sections/1/associate_state/",
                    {'associated_states': ['1', '2']})
        self.assertEqual(section.starting_states.count(), 2)
        self.assertIsNotNone(section.starting_states.get(
            name="Default Starting State"))
        self.assertIsNotNone(section.starting_states.get(
            name="Alternate State"))
