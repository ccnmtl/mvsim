from django.contrib import admin
from django.contrib.admin import site
from main.models import Variable, Configuration, Game, State, UserInput
from main.models import CourseSection
from main.forms import CourseSectionForm


class CourseSectionAdmin(admin.ModelAdmin):
    form = CourseSectionForm

site.register(Variable)
site.register(Configuration)
site.register(UserInput)

site.register(Game)
site.register(State)
site.register(CourseSection, CourseSectionAdmin)
