# coding: utf-8

from django.shortcuts import redirect, render
from django.http import Http404
from .models import Answer, Question
from .forms import AskForm, AnswerForm
from random import choice
# import eh
import main_process
import question_parser as qs
import synonym
import ancestors as anc
import time
import random
from ehownet import synonym, ancestors


# Create your views here.

def group():
    grp = []
    size = 1
    answers = Answer.objects.all()
    for i in range(len(answers) / size):
        grp.append(answers[i*size : (i+1)*size])
    return grp

def game(request):
    answers = Answer.objects.all()
    answer = choice(answers)
    for ans in answers:
        if ans.name == u'閃電':
            answer = ans
            break
    form = AskForm()
    contexts = {
        'answer': answer.name,
        'prev': 'PREV',
        'form': form,
        'answers': group()
    }
    return render(request, 'game/game.html', contexts)
    
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

def get_result(request):
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
            syns = synonym.synonym(answer) + [answer]
            start = time.clock()
            success = len(set(syns) & set(keywords)) > 0 or \
                     1 in [ancestors.belong(kwd, answer) for kwd in keywords]
            end = time.clock()
            print "check answer time consuming: ",end - start

            if not success:
                #result = question + ' ' + eh.run(answer, question)
                update = prev == 'PREV'
                #print 'update', update, '!!!!!!!!!'
                #print prev.decode('utf-8').encode('mbcs')
                start = time.clock()
                responder = main_process.Responder()
                end = time.clock()
                print "Responder construction consuming: ",end - start
                result = responder.process(answer, question, update)
                res = 'TEST'
                if(result[0] == 'Y'):
                    if(float(result[2]) > 0.9):
                        res_list = ['沒錯', '是的', 'You\'re right', '嗯，'+question.replace('嗎', '')]
                        res = res_list[random.randrange(len(res_list))]
                    elif(float(result[2]) > 0.7):
                        res_list = ['我想是吧', '應該是', '嗯，我有七成的自信說是']
                        res = res_list[random.randrange(len(res_list))]
                    else:
                        res_list = ['我不是很有自信，但可能是', '大概吧', '我猜可能是吧']
                        res = res_list[random.randrange(len(res_list))]
                elif(result[0] == 'N'):
                    if(float(result[2]) > 0.9):
                        res_list = ['還差得遠呢', '你想太多了', '不是喔']
                        res = res_list[random.randrange(len(res_list))]
                    elif(float(result[2]) > 0.7):
                        res_list = ['我認為不是', '應該不是', '嗯，我有七成的自信說它不是']
                        res = res_list[random.randrange(len(res_list))]
                    else:
                        res_list = ['我不是很有自信，但可能不是吧', '大概不是吧', '應該不是吧', '我猜可能不是吧']
                        res = res_list[random.randrange(len(res_list))]
                prev += '|' + question + ',' + result[0] + ',' + str(float(result[2][:5])*100) + ',' + res

            else:
                prev += '|' + question + ',AC,1,' + '哇，你答對了~~~'

            prev_list = [ s.split(',') for s in prev.split('|')[1:] ]
            cnt = 0
            for i in range(len(prev_list)):
                if prev_list[i][0] != '':
                    cnt += 1
                    prev_list[i].append(cnt)
                else:
                    prev_list[i].append('')

            encourage = True
            if cnt > 3:
                for i in range(-1, -5, -1):
                    if prev_list[i][1] != 'N':
                        encourage = False
            else:
                encourage = False

            if encourage:
                res_list = ['再想想看:)', '加油啊，你可以的~', '再猜猜看:)', '不要氣餒:)']
                res = res_list[random.randrange(len(res_list))]
                prev += '|,,,' + res
                prev_list.append(['', '', '', res, ''])

            contexts = {
                'answer': answer,
                # 'result': result,
                'prev': prev,
                'prev_list': prev_list,
                'success': success,
                'answers': group()
            }

            return render(request, 'game/game.html', contexts)
    else:
        form = AskForm()
    
    return render(request, 'game/game.html', {'result': 'error: get_result', 'form': form})

'''
            if not success:
                # result = question + ' ' + eh.run(answer, question)
                update = prev == 'PREV'
                responder = main_process.Responder()
                result, source, conf = responder.process(answer, question, update)
                prev += '|' + question + ' ' + result + ' ' + conf[:5]

                ques = Question.objects.create(
                    answer=Answer.objects.get(name=answer),
                    name=question,
                    result=', '.join([result, source, conf[:5]])
                )
                ques.save()
'''