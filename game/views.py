# coding: utf-8

from django.shortcuts import redirect, render, render_to_response
from django.http import Http404,HttpResponse
from .models import Answer, Question, Game, ParsedQuestion
from .forms import AskForm, AnswerForm
import time
import random
import re
import sys
from src import main_process
from src import question_parser as qs
from src.ehownet import synonym, ancestors, climb, parse_eh
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
    answers = Answer.objects.all()
    answer = random.choice(answers)
    
    # for debugging
    tmp = u''
    for ans in answers:
        if ans.name == tmp:
            answer = ans
            break
    print(answer.name.encode(sys.getfilesystemencoding()))
    answer = answer.name.encode('utf-8')

    game = Game.objects.create(answer = Answer.objects.get(name=answer))
    game.save()

    # all_hints = get_hints(answer)
    # print 'all hints:', ','.join(all_hints)
    # sims = [getSimilarity(answer, hint) for hint in all_hints]
    # hints_sims = [h_s for h_s in zip(all_hints, sims) if h_s[1]]
    # sorted_hints_sims = sorted(hints_sims, key=lambda h_s: h_s[1], reverse=True)
    # print 'chosen hints:'
    # chosen_hints = []
    # for h, s in sorted_hints_sims:
    #     if set(h.decode('utf-8')) & set(answer.decode('utf-8')) == set():
    #         print h, s
    #         chosen_hints.append(h)
    # chosen_hints = chosen_hints[:3]
    
    form = AskForm()
    contexts = {
        'answer': answer,
        'prev': 'PREV',
        'scroll_pos': 0,
        'used_hints': '',
        'form': form,
        'answers': group(),
        'game_id' : game.id
    }

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
        # form = AskForm(request.POST)
        # data = form.cleaned_data
        # answer = data['answer'].encode('utf-8')
        # prev = data['prev'].encode('utf-8')
        # success = data['success']
        # scroll_pos = data['scroll_pos']
        # hints_concat = data['hints_concat']
        # used_hints = data['used_hints']
        # game_id = game['game_id']
        # question = data['question'].encode('utf-8')
        answer = request.POST.get('answer').encode('utf-8')
        question = request.POST.get('question').encode('utf-8')
        game_id =  request.POST.get('game_id')

        # print 'POST data:'
        # for k in data:
        #     print '\t', k, data[k]
        # print "get data:",time.clock()-earliest
        print answer.decode('utf-8').encode(sys_type)
        print question.decode('utf-8').encode(sys_type)
        # print "preparation:",time.clock()-earliest
        
        responder = main_process.Responder()
        print "responder construction:",time.clock()-earliest
        result_ls = responder.process(answer, question, not responder.has_updated)
        print "responder.process:",time.clock()-earliest

        result_ls.sort(key=lambda x:x.label, reverse=True) #sort by Y/N                        
        response_list = []
        success = False
        pre_label =None

        for i, result in enumerate(result_ls):
            print("aaaaaaaaaa")
            response = {}
            if result.label == 'AC':
                response['dialog'] = '答對了！答案就是「' + answer + '」'
                response['record'] = [question, 'AC', 1]
                success = True

            elif result.label == 'illegal':
                response['dialog'] = '你的問題必須包含「它」喔~'

            elif result.label == '?':
                response['dialog'] = '我聽不懂你在說什麼QQ'
                response['record'] = [question,'?',1]

            else:
                # ehownetPath = 'resources/eHowNet_utf8.csv'
                # parser = qs.question_parser(ehownetPath)
                # neg = parser.isNegativeSentence(question)
                neg = result.is_neg
                if (result.label == 'Y' and not neg) or (result.label == 'N' and neg):
                    if(float(result.conf) > 0.9):
                        res_list = ['沒錯', '是的', '對']
                    elif(float(result.conf) > 0.7):
                        pre_sentences_list = ['我想是吧', '應該是']
                    else:
                        pre_sentences_list = ['我不是很有自信，但可能是', '大概吧', '我猜可能是吧']
                else:
                    if(float(result.conf) > 0.9):
                        pre_sentences_list = ['我很遺憾', '不對喔', '你想太多了', '不是喔']
                    elif(float(result.conf) > 0.7):
                        pre_sentences_list = ['我認為不是', '應該不是']
                    else:
                        pre_sentences_list = ['我不是很有自信，但可能不是吧', '大概不是吧', '應該不是吧', '我猜可能不是吧']
                pre_sentence = pre_sentences_list[random.randrange(len(pre_sentences_list))]

                if len(result_ls)==1: 
                    #if there is only one result, then append pre_sentence
                    response['dialog'] = "{}，{}".format(pre_sentence,result.answer_str)
                else:
                    if i==0:
                        response['dialog'] = result.answer_str                        
                    else:
                        if pre_label == result.label:
                            conj = '也'
                        else:
                            conj = '但'
                        response['dialog'] = conj + result.answer_str.replace('它','')

                response['record'] = [result.new_question, result.label, format(float(result.conf)*100, '.2f')]
            
            # insert into DB
            game = Game.objeces.get(id=game_id)
            parse_qt = ParsedQuestion.objects.create(
                content = question
                #TODO: save parsed result
            )
            qo = Question.objects.create(
                game_id = game,
                content = parse_qt,
                result = result.label
            )
            parse_qt.save()
            qo.save()
            response_list.append(response)
            pre_label = result.label

        # encourage = True
        # if cnt > 2:
        #     for i in range(-1, -4, -1):
        #         if prev_list[i][1] != 'N':
        #             encourage = False
        # else:
        #     encourage = False

        # if encourage:
        #     defs = climb.climb(answer, strict=False, shorter=True)
        #     if defs == []:
        #         pre_sentences_list = ['再想想看:)', '加油啊，你可以的~', '再猜猜看:)', '不要氣餒:)']
        #         res = pre_sentences_list[random.randrange(len(res_list))]
        #     else:
        #         definition = defs[0]
        #         definition = re.sub('(\|\w+)|(\w+\|)', '', definition)
        #         def_root = parse_eh.parse(definition)
        #         max_depth = def_root.get_depth()
        #         res = parse_eh.def2sentence(def_root, max_depth)
        #     prev += '|,,,' + res
        #     prev_list.append(['', '', '', res, ''])
        
        # chosen_hints = hints_concat.split('|')
        
        contexts = {
            'answer': answer,
            # 'prev': prev,
            # 'success': success,
            # 'scroll_pos': scroll_pos,
            # 'used_hints': used_hints,
            # 'chosen_hints': chosen_hints,
            # 'prev_list': prev_list,
            # 'answers': group(),
            'game_id':game.id,
            'response_list':response_list
        }
        latest = time.clock()
        print "total time:", latest-earliest
        # return render(request, 'game/game.html', contexts)
        # return render_to_response("game/game.html", RequestContext(request, contexts))
        print("hi")
        return HttpResponse(json.dumps(contexts),content_type="application/json")
    
    return HttpResponse({error:True},content_type="application/json")
    # return render(request, 'game/game.html', {'result': 'error: get_result', 'form': form})
