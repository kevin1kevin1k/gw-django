# coding: utf-8

from django.shortcuts import redirect, render
from django.http import Http404
from .models import Answer
from .forms import AskForm, AnswerForm
from random import choice
import eh

# Create your views here.

def game(request):
    answers = Answer.objects.all()
    answer = choice(answers)
    form = AskForm()
    return render(request, 'game/game.html', {'word': answer.name, 'form': form})
    
def answer_list(request):
    answers = Answer.objects.all()
    return render(request, 'game/answer_list.html', {'answers': answers})

def answer_detail(request, pk):
    try:
        answer = Answer.objects.get(pk=pk)
    except Store.DoesNotExist:
        raise Http404
    return render(request, 'game/answer_detail.html', {'answer': answer})

def answer_create(request):
    if request.method == 'POST':
        form = AnswerForm(request.POST, submit_title='新增')
        if form.is_valid():
            answer = form.save()
            return redirect(answer.get_absolute_url())
    else:
        form = AnswerForm(submit_title='新增')
    return render(request, 'game/answer_create.html', {'form': form})

def get_name(request):
    if request.method == 'POST':
        form = AskForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            # prev = data['prev']
            name = data['your_name']
            ans = eh.run('鯨魚', name)
            # prev + ' ' + name + ' ' + ans
            return render(request, 'game/game.html', {'word': str(data) + ' ' + name + ' ' + ans})
    else:
        form = AskForm()
    
    return render(request, 'game/game.html', {'word': 'haha'})
