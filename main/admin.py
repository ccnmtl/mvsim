from main.models import *
from django.contrib.admin import site

site.register(Variable)
site.register(Configuration)
site.register(UserInput)

site.register(Game)
site.register(State)
site.register(CourseSection)
