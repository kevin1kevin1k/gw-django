# coding: utf-8

from django.shortcuts import redirect, render
from django.http import Http404
from .models import Answer
from .forms import AskForm, AnswerForm
from random import choice
# import eh
import main_process
import question_parser as qs
import synonym

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
        form = AnswerForm(request.POST)
        if form.is_valid():
            answer = form.save()
            return redirect(answer.get_absolute_url())
    else:
        form = AnswerForm()
    return render(request, 'game/answer_create.html', {'form': form})

def get_name(request):
    if request.method == 'POST':
        form = AskForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            answer = data['answer'].encode('utf-8')
            prev = data['prev'].encode('utf-8')
            question = data['question'].encode('utf-8')
            
            ehownetPath = 'eHowNet_utf8.csv'
            parser = qs.question_parser(ehownetPath)
            keywords, qtype = parser.parse_question(question)
            syns = synonym.synonym(answer)
            success = len(set(syns) & set(keywords)) > 0
            if not success:
                # result = question + ' ' + eh.run(answer, question)
                update = 'PREV' in prev
                responder = main_process.Responder()
                result = question + ' ' + responder.process(answer, question, update)
                prev += '|' + result
                if 'PREV|' in prev:
                    prev = prev[5:]
            prev_list = [s.split(' ') for s in prev.split('|')]
            prev_len = len(prev_list)
            for i in range(prev_len):
                prev_list[i].append(i+1)
            contexts = {
                'answer': answer,
                # 'result': result,
                'prev': prev,
                'prev_list': prev_list,
                'success': success
            }
            return render(request, 'game/game.html', contexts)
    else:
        form = AskForm()
    
    return render(request, 'game/game.html', {'result': 'error: get_name', 'form': form})
