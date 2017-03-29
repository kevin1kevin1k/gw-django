# coding: utf-8

from django.shortcuts import redirect, render, render_to_response
from django.http import Http404,HttpResponse
from .models import Answer, Question, Game, Original_Question, Hint
from .forms import AskForm, AnswerForm
import time
import random
import re
import sys
import json
from ipware.ip import get_ip
from src import main_process
from src import question_parser as qs
from src.ehownet import synonym, ancestors, climb, parse_eh
from src import crawl_wiki
from src.crawlData import getSimilarity
from src.TranslationTool import google_translate as gt

# def get_hints(answer):    
#     anc_words = ancestors.anc(answer)
    
#     eh_words = []
#     stop_words = [answer, '有']
#     for word in climb.climb_words(answer):
#         if word not in stop_words and '值' not in word:
#             eh_words.append(word)
    
#     wikidict = crawl_wiki.load_pkl_to_dict('resources/answer200.pkl')
#     word2depth = wikidict.get(answer, {})
#     wiki_words = word2depth.keys()
#     if answer in wiki_words:
#         wiki_words.remove(answer)
    
#     return list(set(anc_words + eh_words + wiki_words))

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
    name = answer.name
    name_en = answer.name_en
    answer = answer.name.encode('utf-8')

    ip = get_ip(request)
    if ip is None:
        ip = ""

    game = Game.objects.create(answer = Answer.objects.get(name=answer),source_ip = ip)
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

    contexts = {
        'answer': name,
        'answer_en': name_en,
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
        games = answer.games.all()
        question_list =[]
        for game in games:
            question_list.extend(game.questions.all())
    except Answer.DoesNotExist:
        raise Http404
    return render(request, 'game/answer_detail.html', {'answer': answer,'questions':question_list})

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

        if request.LANGUAGE_CODE == 'en':
            print('english mode!')
            question_origin = question
            if '?' not in question:
                question = question+'?'
            question = question.replace('it','he')                
            question = gt.translate(question,sl='en',tl='zh-tw')
            question = question.replace('？','').replace('?','')
            if '他' not in question and '它' not in question and len(question.decode('utf-8'))>3:
                question = '它'+question


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
        response_dialog = ""
        record_list=[]
        success = False
        pre_label =None
        
        #DB
        game = Game.objects.get(id=game_id)
        original_qt,created = Original_Question.objects.get_or_create(
                content = question
                #TODO: save parsed result
            )
        game.original_questions.add(original_qt)
        original_qt.save()
        
        for i, result in enumerate(result_ls):
            small_q = question
            
            if result.label == 'AC':
                response_dialog = '答對了！答案就是「' + answer + '」'
                record_list.append([question, 'AC', 1])
                success = True

            elif result.label == 'illegal':
                response_dialog = '你的問題必須包含「它」喔~'

            elif result.label == '?':
                response_dialog = '我聽不懂你在說什麼QQ'
                record_list.append([question,'?',1])

            else:
                # ehownetPath = 'resources/eHowNet_utf8.csv'
                # parser = qs.question_parser(ehownetPath)
                # neg = parser.isNegativeSentence(question)
                neg = result.is_neg
                if (result.label == 'Y' and not neg) or (result.label == 'N' and neg):
                    if(float(result.conf) > 0.9):
                        pre_sentences_list = ['沒錯', '是的', '對']
                    elif(float(result.conf) > 0.7):
                        pre_sentences_list = ['我想是吧', '應該是']
                    else:
                        pre_sentences_list = ['大概吧', '我猜可能是吧']
                else:
                    if(float(result.conf) > 0.9):
                        pre_sentences_list = ['我很遺憾', '不對喔', '不是喔']
                    elif(float(result.conf) > 0.7):
                        pre_sentences_list = ['我認為不是', '應該不是']
                    else:
                        pre_sentences_list = ['大概不是吧', '應該不是吧', '我猜可能不是吧']
                pre_sentence = pre_sentences_list[random.randrange(len(pre_sentences_list))]

                if len(result_ls)==1: 
                    #if there is only one result, then append pre_sentence
                    response_dialog = "{}，{}".format(pre_sentence,result.answer_str)
                else:
                    if i==0:
                        response_dialog = result.answer_str                        
                    else:
                        if pre_label == result.label:
                            conj = '也'
                        else:
                            conj = '但'
                        response_dialog += conj + result.answer_str.replace('它','')

                #if there are multiple keywords, seperate the question into multiple sentence
                small_q = result.answer_str.replace('不', '').replace('沒有', '有').replace('無關', '有關')+'嗎'   
                if request.LANGUAGE_CODE == 'en':
                    if small_q != question.replace('他','它'):
                        small_q = gt.translate(small_q,sl='zh-tw',tl='en')                       
                    else:
                        small_q = question_origin
                record_list.append([small_q, result.label, format(float(result.conf)*100, '.2f')])
                
            # insert into DB
            if success:
                game.is_finished =True
                
            #if one sentence contains multiple keywords, it will be saved seperatedly
            qo = Question.objects.create(
                game = game,
                content = small_q,
                label = result.label,
                source = result.source,
                confidence_score = result.conf
            )
            qo.save()
            pre_label = result.label
            if result.label != 'Y' and result.label !='AC':
                overall_lable = 'N'

        #hint
        # encourage = False
        # hint=''
        # question_hist = game.questions.all().order_by('id')
        # question_count = question_hist.count()
        # # if question_count >= 3:
        # #     consev_N = True
        # #     for i in range(question_count-1, question_count-4, -1): 
        # #         # if there are three consecutive N, give hints to users
        # #         if question_hist[i].label != 'N':
        # #             consev_N = False
        # #     if consev_N:
        # #         encourage=True
        # n_count = sum([1 if q.label=='N' else 0 for q in question_hist])
        # if n_count == 3 and question_hist[question_count-1].label == 'N' :
        #     anc_words = ancestors.anc(answer)
        #     anc = anc_words[0]
        #     hint ='給你一點提示， 它是' + anc + '的一種'
        #     game.hint_used = 'Ancestor'
        #     # encourage = True
        # elif n_count == 6 and question_hist[question_count-1].label == 'N':
        #     defs = climb.climb(answer, strict=False, shorter=True)
        #     if defs == []:
        #         encourage_list = ['再想想看:)', '加油啊，你可以的~', '再猜猜看:)', '不要氣餒:)']
        #         hint = encourage_list[random.randrange(len(encourage_list))]
        #     else:
        #         definition = defs[0]
        #         definition = re.sub('(\|\w+)|(\w+\|)', '', definition)
        #         def_root = parse_eh.parse(definition)
        #         max_depth = def_root.get_depth()
        #         hint = '給你一點提示， 它是' + parse_eh.def2sentence(def_root, max_depth)
        #         game.hint_used = 'Sentence'
        
        game.save()

        contexts = {
            'success':success,
            'response_dialog':response_dialog,
            'record_list':record_list,
            # 'hint':hint,
            'question_trans':'',
            'response_dialog_trans':'',
            # 'hint_trans':''
        }
        if request.LANGUAGE_CODE == 'en':
            dialog_en = []
            for subs in response_dialog.split('，'):
                dialog_en.append(gt.translate(subs,sl='zh-tw',tl='en'))
            response_dialog_en = ','.join(dialog_en)

            contexts['question_trans'] = question
            contexts['response_dialog_trans'] = response_dialog_en

            # if hint:
            #     hint_en_sub= []
            #     for subs in hint.split('，'):
            #         hint_en_sub.append(gt.translate(subs,sl='zh-tw',tl='en'))
            #     hint_en = ','.join(hint_en_sub)
            #     contexts['hint_trans'] = hint_en

        latest = time.clock()
        print "total time:", latest-earliest
        # return render(request, 'game/game.html', contexts)
        # return render_to_response("game/game.html", RequestContext(request, contexts))
        return HttpResponse(json.dumps(contexts),content_type="application/json")
    
    return HttpResponse({error:True},content_type="application/json")
    # return render(request, 'game/game.html', {'result': 'error: get_result', 'form': form})

def get_hint(request):
    if request.method == 'POST':
        game_id =  request.POST.get('game_id')
        answer =  request.POST.get('answer').encode('utf-8')
        game = Game.objects.get(id=game_id)

        hint_count = game.hints.all().count()     
        hint = ''
        name = ''
        if hint_count == 0: #上位

            anc_words = ancestors.anc(answer)
            anc = anc_words[0]
            hint ='它是' + anc + '的一種'
            name ='ancestor'

        elif hint_count == 1: #定義式
            defs = climb.climb(answer, strict=False, shorter=True)
            if defs:
                definition = defs[0]
                definition = re.sub('(\|\w+)|(\w+\|)', '', definition)
                def_root = parse_eh.parse(definition)
                max_depth = def_root.get_depth()
                hint = '它是' + parse_eh.def2sentence(def_root, max_depth)
                name = 'definition sentence'

        elif hint_count == 2: #10選1
            answers_count = Answer.objects.all().count()
            answer_id = game.answer
            all_ids = [i+1 for i in range(answers_count) if i !=answer_id]
            random.shuffle(all_ids)
            candidate_ids = all_ids[0:9]
            candidate_ans = Answer.objects.filter(id__in=candidate_ids)
            candidate_ans = [a.name.encode('utf-8') for a in candidate_ans] + [answer]
            random.shuffle(candidate_ans)
            candidate_str = ', '.join(candidate_ans) 
            hint = '答案就在其中:' + candidate_str
            name = 'multiple choice'
        
        if hint:
            qcount = game.questions.all().count()
            hint_obj = Hint.objects.create(
                    game = game,
                    name = name,
                    content = hint,
                    pre_questions_count = qcount
            )
            hint_obj.save()

        #translation
        print(hint)
        if request.LANGUAGE_CODE == 'en': 
            hint = hint.replace(',',' ')
            hint = gt.translate(hint,sl='zh-tw',tl='en')
            print(hint)

        contexts ={'hint' : hint}
        return HttpResponse(json.dumps(contexts),content_type="application/json")
        