from django import forms
from mvsim.main.models import (CourseSection,
                               State)


class CourseSectionForm(forms.ModelForm):
    class Meta:
        model = CourseSection

    def __init__(self, *args, **kw):
        forms.ModelForm.__init__(self, *args, **kw)
        # https://github.com/ccnmtl/mvsim/issues/1
        self.fields['starting_states'].queryset = State.objects.filter(
            game__isnull=True)
