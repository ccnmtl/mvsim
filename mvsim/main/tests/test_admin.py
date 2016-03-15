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
        self.assertEquals(len(course.coursesection_set.all()), 1)

        section = CourseSection.objects.get(id=1)
        self.assertEquals(section.name, 'Default Section')

        self.assertEquals(len(section.starting_states.all()), 1)
        state = section.starting_states.get(id=1)
        self.assertEquals('Default Starting State', state.name)

        state = State.objects.get(id=1)
        self.assertEquals(state.visible, True)
        self.assertEquals(len(state.coursesection_set.all()), 1)

    def test_edit_state_access(self):
        client = Client()
        u = User.objects.get(username='test_instructor')
        u.set_password('test')
        u.save()

        self.assertTrue(
            client.login(username='test_instructor', password='test'))

        response = client.get("/state/1/")
        self.assertEquals(response.status_code, 403)
        response = client.post("/state/1/edit/")
        self.assertEquals(response.status_code, 403)
        response = client.post("/state/1/clone/")
        self.assertEquals(response.status_code, 403)

        u = User.objects.get(username='test_student_one')
        u.set_password('test')
        u.save()

        self.assertTrue(
            client.login(username='test_student_one', password='test'))
        response = client.get("/state/1/")
        self.assertEquals(response.status_code, 403)
        response = client.post("/state/1/edit/")
        self.assertEquals(response.status_code, 403)
        response = client.post("/state/1/clone/")
        self.assertEquals(response.status_code, 403)

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
        self.assertEquals(state.visible, True)
        self.assertEquals(len(state.coursesection_set.all()), 1)

        client.post("/state/1/edit/", {u'visible': [u'True'],
                                       u'associated_sections': [u'1']})
        state = State.objects.get(id=1)
        self.assertEquals(state.visible, True)

        client.post("/state/1/edit/", {u'visible': [u'False'],
                                       u'associated_sections': [u'1']})
        state = State.objects.get(id=1)
        self.assertEquals(state.visible, False)

        client.post("/state/1/edit/", {u'visible': [u'False'],
                                       u'associated_sections': [u'1']})
        state = State.objects.get(id=1)
        self.assertEquals(state.visible, False)

        client.post("/state/1/edit/", {'visible': "True",
                                       u'associated_sections': [u'1']})
        state = State.objects.get(id=1)
        self.assertEquals(state.visible, True)
        self.assertEquals(len(state.coursesection_set.all()), 1)

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
        self.assertEquals(state.visible, True)
        self.assertEquals(len(state.coursesection_set.all()), 1)
        self.assertEquals(state.coursesection_set.all()[0].name,
                          "Default Section")

        client.post("/state/1/edit/", {u'associated_sections': [u'1']})
        self.assertEquals(len(state.coursesection_set.all()), 1)
        self.assertEquals(state.coursesection_set.all()[0].name,
                          "Default Section")

        client.post("/state/1/edit/", {})
        state = State.objects.get(id=1)
        self.assertEquals(len(state.coursesection_set.all()), 0)

        client.post("/state/1/edit/", {'associated_sections': []})
        state = State.objects.get(id=1)
        self.assertEquals(len(state.coursesection_set.all()), 0)

        client.post("/state/1/edit/", {'associated_sections': [u'1']})
        state = State.objects.get(id=1)
        self.assertEquals(len(state.coursesection_set.all()), 1)
        self.assertEquals(state.coursesection_set.all()[0].name,
                          "Default Section")

        state = State.objects.get(id=1)
        self.assertEquals(state.visible, True)

    def test_clone_state(self):
        self.assertEquals(len(State.objects.all()), 2)
        starting_states = CourseSection.objects.get(id=1).starting_states.all()
        self.assertEquals(len(starting_states), 1)

        client = Client()
        u = User.objects.get(username='admin')
        u.set_password('admin')
        u.save()

        self.assertTrue(
            client.login(username='admin', password='admin'))

        response = client.get("/state/1/")
        self.assertTemplateUsed(response, "admin/view_state.html")

        client.post("/state/1/clone/",
                    {u'visible': [u'False'],
                     u'associated_sections': [u'1'],
                     u'state_name': [u'New State']})

        self.assertTemplateUsed(response, "admin/view_state.html")
        self.assertEquals(len(State.objects.all()), 3)
        new_state = State.objects.get(name="New State")
        self.assertFalse(new_state.visible)
        self.assertEquals(len(new_state.coursesection_set.all()), 1)
        self.assertEquals(new_state.coursesection_set.all()[0].name,
                          "Default Section")
        starting_states = CourseSection.objects.get(id=1).starting_states.all()
        self.assertEquals(len(starting_states), 2)
        self.assertEquals(starting_states[1], new_state)

        client.post("/state/1/clone/",
                    {u'visible': [u'True'],
                     u'state_name': [u'Another New State']})

        self.assertTemplateUsed(response, "admin/view_state.html")
        self.assertEquals(len(State.objects.all()), 4)
        new_state = State.objects.get(name="Another New State")
        self.assertTrue(new_state.visible)
        self.assertEquals(len(new_state.coursesection_set.all()), 0)

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
                    {u'associated_states': [u'1']})
        self.assertEqual(section.starting_states.count(), 1)
        self.assertEqual(section.starting_states.all()[0].name,
                         "Default Starting State")

        client.post("/course_sections/1/associate_state/",
                    {u'associated_states': []})
        self.assertEqual(section.starting_states.count(), 0)

        client.post("/course_sections/1/associate_state/",
                    {u'associated_states': [u'1']})
        self.assertEqual(section.starting_states.count(), 1)
        self.assertEqual(section.starting_states.all()[0].name,
                         "Default Starting State")

        client.post("/course_sections/1/associate_state/", {})
        self.assertEqual(section.starting_states.count(), 0)

        client.post("/course_sections/1/associate_state/",
                    {u'associated_states': [u'1', u'2']})
        self.assertEqual(section.starting_states.count(), 2)
        self.assertIsNotNone(section.starting_states.get(
            name="Default Starting State"))
        self.assertIsNotNone(section.starting_states.get(
            name="Alternate State"))
