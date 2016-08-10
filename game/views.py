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
    tmp = u'學生'
    for ans in answers:
        if ans.name == tmp:
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
            keywords_dict = parser.parse_question(question)
            syns = synonym.synonym(answer) + [answer]
            start = time.clock()
            class_exist = False
            for key in keywords_dict:
                if key == 'class':
                    class_exist = True
            print 'class', class_exist
            success = False
            if class_exist:
                success = len(set(syns) & set(keywords_dict['class'])) > 0 or \
                         1 in [ancestors.belong(kwd, answer) for kwd in keywords_dict['class']]
            end = time.clock()
            print "check answer time consuming: ",end - start

            if not success:
                #result = question + ' ' + eh.run(answer, question)
                update = prev == 'PREV'
                start = time.clock()
                responder = main_process.Responder()
                end = time.clock()
                print "Responder construction consuming: ",end - start
                result_ls = responder.process(answer, question, update)

                Y_num = 0
                N_num = 0
                for result in result_ls:
                    if result[2] == 'Y':
                        Y_num += 1
                    elif result[2] == 'N':
                        N_num += 1
                    ques = Question.objects.create(
                        answer=Answer.objects.get(name=answer),
                        name=result[5].replace('不', '')+'嗎',
                        result=', '.join([result[2], result[4], result[3][:5]])
                    )
                    ques.save()

                res = 'TEST'
                if len(result_ls) == 1:
                    result = result_ls[0]
                    if Y_num > 0 or N_num > 0:
                        if Y_num > 0:
                            if(float(result[3]) > 0.9):
                                res_list = ['沒錯', '是的', '對']
                                res = res_list[random.randrange(len(res_list))]
                            elif(float(result[3]) > 0.7):
                                res_list = ['我想是吧', '應該是', '嗯，我有七成的自信']
                                res = res_list[random.randrange(len(res_list))]
                            else:
                                res_list = ['我不是很有自信，但可能是', '大概吧', '我猜可能是吧']
                                res = res_list[random.randrange(len(res_list))]
                        else:
                            if(float(result[3]) > 0.9):
                                res_list = ['還差得遠呢', '你想太多了', '不是喔']
                                res = res_list[random.randrange(len(res_list))]
                            elif(float(result[3]) > 0.7):
                                res_list = ['我認為不是', '應該不是', '嗯，我有七成的自信']
                                res = res_list[random.randrange(len(res_list))]
                            else:
                                res_list = ['我不是很有自信，但可能不是吧', '大概不是吧', '應該不是吧', '我猜可能不是吧']
                                res = res_list[random.randrange(len(res_list))]
                        prev += '|' + question + ',' + result[2] + ',' + str(format(float(result[3])*100, '.2f')) + ',' + res + '，' + result[5]
                    else:
                        prev += '|' + question + ',' + result[2] + ',' + '0' + ',' + '我聽不懂你在說什麼QQ'
                else:
                    Y_cnt = 0
                    N_cnt = 0
                    for result in result_ls:
                        if(result[2] == 'Y'):
                            Y_cnt += 1
                            if Y_cnt == 1:
                                res = result[5]
                            elif Y_cnt == Y_num:
                                res = res + '，也' + result[5].replace('它', '')
                            else:
                                res = res + '，' + result[5].replace('它', '')
                    for result in result_ls:
                        if(result[2] == 'N'):
                            N_cnt += 1
                            if N_cnt == 1:
                                if Y_num == 0:
                                    res = result[5]
                                else:
                                    res = res + '，但' + result[5]
                            elif N_cnt == N_num:
                                res = res + '，也' + result[5].replace('它', '')
                            else:
                                res = res + '，' + result[5].replace('它', '')
                    prev += '|' + question + ',' + '' + ',' + '' + ',' + res
                    for result in result_ls:
                        prev += '|' + result[5].replace('不', '') + '嗎' + ',' + result[2] + ',' + str(format(float(result[3])*100, '.2f')) + ',' + ''
            else:
                prev += '|' + question + ',AC,100.0,' + '哇，你答對了~~~'

            prev_list = [ s.split(',') for s in prev.split('|')[1:] ]
            cnt = 0
            for i in range(len(prev_list)):
                if prev_list[i][1] != '':
                #''->encourage, 'X'->various question
                    cnt += 1
                    prev_list[i].append(cnt)
                else:
                    prev_list[i].append('')

            encourage = True
            if cnt > 2:
                for i in range(-1, -4, -1):
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
                    if Y_num > 0 and N_num > 0:
                        prev += '|' + question + ',' + 'Uncertain' + ',' + 'Various Question' + ',' + res
                    elif Y_num > 0:
                        prev += '|' + question + ',' + 'Y' + ',' + 'Various Question' + ',' + res
                    elif N_num > 0:
                        prev += '|' + question + ',' + 'N' + ',' + 'Various Question' + ',' + res
'''

'''
            for s in prev.split('|')[1:]:
                questions = []
                for ques in s.split(';'):
                    questions.append([item for item in ques.split(',')])
                prev_list.append(questions)
'''