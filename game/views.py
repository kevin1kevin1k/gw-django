# coding: utf-8

from django.shortcuts import redirect, render
from django.http import Http404
from .models import Answer
from .forms import AskForm, AnswerForm
from random import choice
# import eh
import main_process

# Create your views here.

def game(request):
    answers = Answer.objects.all()
    answer = choice(answers)
    form = AskForm()
    return render(request, 'game/game.html', {'answer': answer.name, 'prev': 'PREV', 'form': form})
    
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
            answer = data['answer']
            prev = data['prev']
            question = data['question']
            # result = question + ' ' + eh.run(answer, question)
            result = question + ' ' + main_process.Responder().process(answer.encode('utf-8'), question.encode('utf-8'))
            prev += '|' + result
            if 'PREV|' in prev:
                prev = prev[5:]
            prev_list = [s.split(' ') for s in prev.split('|')]
            contexts = {
                'answer': answer,
                'result': result,
                'prev': prev,
                'prev_list': prev_list,
                'success': answer in question
            }
            return render(request, 'game/game.html', contexts)
    else:
        form = AskForm()
    
    return render(request, 'game/game.html', {'result': 'error: get_name', 'form': form})
