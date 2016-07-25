from django import forms
from .models import Answer
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

class AskForm(forms.Form):
    # prev = forms.CharField(label="prev", max_length=20)
    your_name = forms.CharField(label="your_name", max_length=20)
    
    # def __init__(self, *args, submit_title='Submit', **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.helper = FormHelper()
    #     if submit_title:
    #         self.helper.add_input(Submit('submit', submit_title))


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['name']
    
    def __init__(self, *args, submit_title='Submit', **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        if submit_title:
            self.helper.add_input(Submit('submit', submit_title))
