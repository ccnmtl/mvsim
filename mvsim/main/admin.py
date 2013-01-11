from django.contrib import admin
from django.contrib.admin import site
from mvsim.main.models import Variable, Configuration, Game, State, UserInput
from mvsim.main.models import CourseSection
from mvsim.main.forms import CourseSectionForm


class CourseSectionAdmin(admin.ModelAdmin):
    form = CourseSectionForm

site.register(Variable)
site.register(Configuration)
site.register(UserInput)

site.register(Game)
site.register(State)
site.register(CourseSection, CourseSectionAdmin)
