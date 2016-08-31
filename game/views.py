# coding: utf-8

from django.shortcuts import redirect, render
from django.http import Http404
from .models import Answer, Question
from .forms import AskForm, AnswerForm
import time
import random
import re
import sys
from src import main_process
from src import question_parser as qs
from src.ehownet import synonym, ancestors, climb
from src import crawl_wiki
from src.crawlData import getSimilarity

def get_hints(answer):    
    anc_words = ancestors.anc(answer)
    
    eh_words = []
    stop_words = [answer, '有']
    for word in climb.climb_words(answer):
        if word not in stop_words and '值' not in word:
            eh_words.append(word)
    
    wikidict = crawl_wiki.load_pkl_to_dict('resources/answer200.pkl')
    word2depth = wikidict.get(answer, {})
    wiki_words = word2depth.keys()
    if answer in wiki_words:
        wiki_words.remove(answer)
    
    return list(set(anc_words + eh_words + wiki_words))

def group():
    grp = []
    size = 1
    answers = Answer.objects.all()
    for i in range(len(answers) / size):
        grp.append(answers[i*size : (i+1)*size])
    return grp

def game(request):
    start = time.clock()
    answers = Answer.objects.all()
    answer = random.choice(answers)
    
    # for debugging
    tmp = u''
    for ans in answers:
        if ans.name == tmp:
            answer = ans
            break
    answer = answer.name.encode('utf-8')
    print answer

    all_hints = get_hints(answer)
    print 'all hints:', ','.join(all_hints)
    sims = [getSimilarity(answer, hint) for hint in all_hints]
    hints_sims = [h_s for h_s in zip(all_hints, sims) if h_s[1]]
    sorted_hints_sims = sorted(hints_sims, key=lambda h_s: h_s[1], reverse=True)
    print 'chosen hints:'
    chosen_hints = []
    for h, s in sorted_hints_sims:
        if set(h.decode('utf-8')) & set(answer.decode('utf-8')) == set():
            print h, s
            chosen_hints.append(h)
    chosen_hints = chosen_hints[:3]
    
    form = AskForm()
    contexts = {
        'answer': answer,
        'prev': 'PREV',
        'scroll_pos': 0,
        'used_hints': '',
        'chosen_hints': chosen_hints,
        'form': form,
        'answers': group()
    }
    end = time.clock()
    print "responder construction time: ",end - start
    return render(request, 'game/game.html', contexts)
    
def answer_list(request):
    answers = Answer.objects.all()
    return render(request, 'game/answer_list.html', {'answers': answers})

def answer_detail(request, pk):
    try:
        answer = Answer.objects.get(pk=pk)
    except Answer.DoesNotExist:
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
    earliest = time.clock()
    sys_type=sys.getfilesystemencoding()
    if request.method == 'POST':
        form = AskForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            answer = data['answer'].encode('utf-8')
            prev = data['prev'].encode('utf-8')
            success = data['success']
            scroll_pos = data['scroll_pos']
            hints_concat = data['hints_concat']
            used_hints = data['used_hints']
            
            question = data['question'].encode('utf-8')
            print 'POST data:'
            for k in data:
                print '\t', k, data[k]
            print "get data:",time.clock()-earliest
            print answer.decode('utf-8').encode(sys_type)
            print "preparation:",time.clock()-earliest
            
            responder = main_process.Responder()
            print "responder construction:",time.clock()-earliest
            result_ls = responder.process(answer, question, not responder.has_updated)
            print "responder.process:",time.clock()-earliest
            
            if len(result_ls) == 1:
                result = result_ls[0]
                if result.label == 'AC':
                    prev += '|' + question + ',AC,,' + '答對了！答案就是「' + answer + '」'   #for both dialog and question table
                    success = True
                elif result.label == 'illegal':
                    prev += '|' + question + ',,,' + '你的問題必須包含\'它\'喔~'    #for dialog
                elif result.label == '?':
                    ques = Question.objects.create(
                        answer=Answer.objects.get(name=answer),
                        name=question,
                        result=', '.join([result.label, result.source, result.conf[:5]])
                    )
                    ques.save()
                    prev += '|' + question + ',' + result.label + ',' + '0' + ',' + '我聽不懂你在說什麼QQ' #for both dialog and question table
                else:
                    ques = Question.objects.create(
                        answer = Answer.objects.get(name=answer),
                        name = result.new_question,
                        result = ', '.join([result.label, result.source, result.conf[:5]])
                    )
                    ques.save()
                    
                    ehownetPath = 'resources/eHowNet_utf8.csv'
                    parser = qs.question_parser(ehownetPath)
                    neg = parser.isNegativeSentence(question)
                    if (result.label == 'Y' and not neg) or (result.label == 'N' and neg):
                        if(float(result.conf) > 0.9):
                            res_list = ['沒錯', '是的', '對']
                        elif(float(result.conf) > 0.7):
                            res_list = ['我想是吧', '應該是', '嗯，我有七成的自信', '嗯，我有七成的把握']
                        else:
                            res_list = ['我不是很有自信，但可能是', '大概吧', '我猜可能是吧']
                    else:
                        if(float(result.conf) > 0.9):
                            res_list = ['我很遺憾', '不對喔', '你想太多了', '不是喔']
                        elif(float(result.conf) > 0.7):
                            res_list = ['我認為不是', '應該不是', '嗯，我有七成的自信', '嗯，我有七成的把握']
                        else:
                            res_list = ['我不是很有自信，但可能不是吧', '大概不是吧', '應該不是吧', '我猜可能不是吧']
                    res = res_list[random.randrange(len(res_list))]
                    
                    if neg:
                        prev += '|' + question + ',' + '' + ',' + '' + ',' + res + '，' + result.answer_str  #for dialog
                        prev += '|' + result.new_question + ',' + result.label + ',' + str(format(float(result.conf)*100, '.2f')) + ',' + ''    #for question table
                    else:
                        prev += '|' + question + ',' + result.label + ',' + str(format(float(result.conf)*100, '.2f')) + ',' + res + '，' + result.answer_str #for both dialog and question table
            else:
                Y_num = 0
                N_num = 0
                for result in result_ls:
                    if result.label == 'Y':
                        Y_num += 1
                    elif result.label == 'N':
                        N_num += 1
                    small_ques = result.answer_str.replace('不', '').replace('沒有', '有').replace('無關', '有關')+'嗎'
                    ques = Question.objects.create(
                        answer=Answer.objects.get(name=answer),
                        name=small_ques,
                        result=', '.join([result.label, result.source, result.conf[:5]])
                    )
                    ques.save()
                    prev += '|' + small_ques + ',' + result.label + ',' + str(format(float(result.conf)*100, '.2f')) + ',' + '' #for question table
                
                Y_cnt = 0
                N_cnt = 0
                for result in result_ls:
                    if(result.label == 'Y'):
                        Y_cnt += 1
                        if Y_cnt == 1:
                            res = result.answer_str
                        elif Y_cnt == Y_num:
                            res = res + '，也' + result.answer_str.replace('它', '')
                        else:
                            res = res + '，' + result.answer_str.replace('它', '')
                for result in result_ls:
                    if(result.label == 'N'):
                        N_cnt += 1
                        if N_cnt == 1:
                            if Y_num == 0:
                                res = result.answer_str
                            else:
                                res = res + '，但' + result.answer_str
                        elif N_cnt == N_num:
                            res = res + '，也' + result.answer_str.replace('它', '')
                        else:
                            res = res + '，' + result.answer_str.replace('它', '')
                prev += '|' + question + ',' + '' + ',' + '' + ',' + res #for dialog
            
            prev_list = [ s.split(',') for s in prev.split('|')[1:] ]
            cnt = 0
            for i in range(len(prev_list)):
                if prev_list[i][1] != '':
                #only the item for question table(have label) would have an id number
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
            
            chosen_hints = hints_concat.split('|')
            
            contexts = {
                'answer': answer,
                'prev': prev,
                'success': success,
                'scroll_pos': scroll_pos,
                'used_hints': used_hints,
                'chosen_hints': chosen_hints,
                'prev_list': prev_list,
                'answers': group()
            }
            latest = time.clock()
            print "total time:", latest-earliest
            return render(request, 'game/game.html', contexts)
    else:
        form = AskForm()
    
    return render(request, 'game/game.html', {'result': 'error: get_result', 'form': form})
