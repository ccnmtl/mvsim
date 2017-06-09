from django.contrib import admin
from django.contrib.admin import site
from mvsim.main.forms import CourseSectionForm
from mvsim.main.models import CourseSection, Category, Variable, \
    Configuration, Game, State, UserInput


class CourseSectionAdmin(admin.ModelAdmin):
    form = CourseSectionForm


class VariableAdmin(admin.ModelAdmin):
    search_fields = ("name", "category__name")
    list_display = ('name', 'category', 'description')


class StateAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ('__unicode__', 'visible')


site.register(CourseSection, CourseSectionAdmin)
site.register(Variable, VariableAdmin)
site.register(Configuration)
site.register(UserInput)
site.register(Game)
site.register(State, StateAdmin)
site.register(Category)
