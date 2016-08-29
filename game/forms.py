# coding: utf-8

from django import forms
from .models import Answer
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

class AskForm(forms.Form):
    answer = forms.CharField()
    prev = forms.CharField()
    success = forms.BooleanField(required=False)
    scroll_pos = forms.IntegerField()
    hints_concat = forms.CharField()
    used_hints = forms.CharField(required=False)
    question = forms.CharField()

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['name']
    
    def __init__(self, *args, **kwargs):
        super(AnswerForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', '新增'))
