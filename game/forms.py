from django import forms
from .models import Answer
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

class AskForm(forms.Form):
    answer = forms.CharField()
    prev = forms.CharField()
    question = forms.CharField()

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['name']
    
    def __init__(self, *args, submit_title='Submit', **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        if submit_title:
            self.helper.add_input(Submit('submit', submit_title))
