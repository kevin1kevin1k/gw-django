#! python2
# -*- coding: UTF-8 -*-

##ref:https://developers.google.com/custom-search/json-api/v1/using_rest#rest_from_javascript
##ref:https://developers.google.com/custom-search/json-api/v1/reference/cse/list#response

from TranslationTool.langconv import *
import urllib
import simplejson
from bs4 import BeautifulSoup
import csv
import sys
import gensim
import os
import time
import sqlite3
import re

####global variable###

model = None
corpusContent = None

######################
def load(model_path):
    '''
    load gensim model and corpusContent into global variable
    '''
    global model
    if model is None:
        model = gensim.models.Word2Vec.load_word2vec_format(model_path, binary = True, unicode_errors = 'ignore')
    global corpusContent
    if corpusContent is None:
        f = open('resources/ASBC.txt', 'r')
        line = f.read()
        sentences = []
        line = line.replace('\n', '')
        for s in line.split('。'):
            sentences.append(unicode(s, 'utf-8'))
            #print s
        corpusContent= sentences

def getSimilarity(w1,w2,model_path="resources/cna_asbc_cbow_d300_w10_n10_hs0_i15.vectors.bin"):
    '''
    Using word embedding model to give consine similarity between two words.
    The main purpose of this function is to prevent repetitive model loading 
    when others need to use word vector similarity.
    '''
    if model is None:
        load(model_path)
    if not isinstance(w1, unicode):
        w1=w1.decode("utf-8")
    if not isinstance(w2, unicode):
        w2=w2.decode("utf-8")       

    if w1 in model and w2 in model:
        sim = model.similarity(w1, w2)
        return sim
    else:
        return None        

def sysPrint(s):
    sys_type=sys.getfilesystemencoding()
    if isinstance(s, unicode):
        print s.encode(sys_type)
    else:          
        print s.decode("utf-8").encode(sys_type)

def checkChinese(sentence):
    for ch in sentence:
        if u'\u4e00' <= ch <= u'\u9fff':
            return True
    return False

def crawlGoogle(answer):
    '''
    If the answer has already been searched, open the data.
    Else search google for 10 pages, then save all the title and snippet.
    '''
    sentences = []    

    filename = answer + '.txt'
    filepath = 'resources/GoogleQueryData/' + filename
    if os.path.exists(unicode(filepath, 'utf-8')):
        f = open(unicode(filepath, 'utf-8'), 'r')
        sysPrint('find '+ filename)
        line = f.read()
        f.close()
        for s in line.split('\n'):
            if s != '':
                sentences.append(unicode(s, 'utf-8'))
    else:
        sysPrint('cannot find the file '+filename)
        search = answer
        #print 'search: ' + search
        
        appKey='AIzaSyCgSBb5QYobtLft2AGa3gdXFeGPDBDuDbM'
        #AIzaSyA0o28200EjisCwc3G5SJ2YLNssMqKquIE
        #AIzaSyAsYhNbtreveTeWLEeyo-g7ntfRDYlrDwY
        #AIzaSyDSayvwpZqS-cs5Kssl_IG-S1tbJWZ8DSc
        #AIzaSyD_BZvojrEmpbEmg2RrehapaGqPxMrn-Xk
        #AIzaSyCgSBb5QYobtLft2AGa3gdXFeGPDBDuDbM
        #000909880606706706095:ygax4u42kpy
        cse_id='013422192935559265541:_o_tz6sazoa'
        for i in range(1, 101, 10):
            query = urllib.urlencode({'key' : appKey,'cx':cse_id,'q':search,'start':i})
            url = 'https://www.googleapis.com/customsearch/v1?%s'%(query)
            #print url
            search_results = urllib.urlopen(url)
            json = simplejson.loads(search_results.read())
            results = json['items']

            for item in results:
                #print item['title']
                #print item['link']
                #print Converter('zh-hant').convert(item['snippet']).encode('utf-8')
                sentences.append(Converter('zh-hant').convert(item['title']).encode('utf-8').replace(" ",""))
                line = Converter('zh-hant').convert(item['snippet']).encode('utf-8')
                for s1 in line.split('.'):
                    for s2 in s1.split('。'):
                        if s2 != '':
                            sentences.append(s2.replace(" ","").replace("\n",""))
        u_sentences = []
        filename = 'resources/GoogleQueryData/' + answer + '.txt'
        f = open(unicode(filename, 'utf-8'), 'w')
        for s in sentences:
            if s != '':
                f.write(s+'\n')
                u_sentences.append(unicode(s, 'utf-8'))
        f.close()

        sentences = u_sentences
    
    return sentences

def crawlWiki(answer):
    '''
    If the answer exist in the Resource.db, open the database.
    Else crawl Wiki page of the answer, then save all the text into Resource.db.
    '''
    sentences = []
    u_answer = unicode(answer, 'utf-8')
    conn = sqlite3.connect('resources/Resource.db')
    try:    #access database
        cursor = conn.execute("SELECT * from WIKI WHERE NAME=?", [u_answer])
        for r in cursor:
            for s in r[1].split('\n'):
                if len(s)>0:
                    sentences.append(s)
        sysPrint( 'Wiki db find '+answer)
    
    except: #crawl
        html = urllib.urlopen("https://zh.wikipedia.org/zh-tw/" + answer)
        soup = BeautifulSoup(html, 'lxml', from_encoding='utf-8')
        for element in soup.find_all('p'):
            for s in element.text.split(u'。'):
                s = re.sub(r'\s|\w', '', s)
                s = s.replace(u'（）', '').replace(u'「」', '').replace(u'[]', '')
                if len(s)>0:
                    sentences.append(s)
        '''
        bodyContent = ''
        for s in soup.find("div", {"id": "bodyContent"}):
            bodyContent += str(s)
        bodyContent = unicode(bodyContent, 'utf-8')
        '''
        body = soup.find("div", {"id": "mw-content-text"})
        for element in body.find_all('ul'):     #divide into different part
            words = ''  #a sentence that contain all the line in the part that no longer than 10 
            for li in element.find_all('li'):   #every line in a part
                text = li.getText()
                text = re.sub(r'\s|\w','', text)
                text = text.replace(u'（）', '').replace(u'「」', '').replace(u'[]', '')
                if checkChinese(text):
                    if len(text) < 10:  #connect to the end of words
                        words += text
                    else:
                        for s in text.split(u'。'):
                            if len(s)>0:
                                sentences.append(s)
            if len(words)>0:
                sentences.append(words)
        ###insert to db###
        data = ''
        for s in sentences:
            data = data + '\n' + s
        conn.execute("INSERT INTO WIKI(NAME, DATA)VALUES(?, ?)", [u_answer, data])
        conn.commit()
        
    conn.close()
    return sentences

def crawlCorpus(answer):
    '''
    If the answer exist in the Resource.db, open the database.
    Else find out all the sentences that contain the answer, then save them into Resource.db.
    '''
    sentences = []
    u_answer = unicode(answer, 'utf-8')
    conn = sqlite3.connect('resources/Resource.db')
    try:    #access database
        cursor = conn.execute("SELECT * from CORPUS WHERE NAME=?", [u_answer])
        for r in cursor:
            for s in r[1].split('\n'):
                if len(s)>0:
                    sentences.append(s)
        sysPrint('Corpus db find '+ answer)
        
    except:
        global corpusContent
        if corpusContent is None:
            f = open('resources/ASBC.txt', 'r')
            line = f.read()
            sentences = []
            line = line.replace('\n', '')
            for s in line.split('。'):
                sentences.append(unicode(s, 'utf-8'))
                #print s
            corpusContent= sentences
        if not isinstance(answer, unicode):    
            answer=unicode(answer,"utf-8")
        targetSentences=[]
        for sentence in corpusContent:
            check = sentence.split(' ')
            if answer in check:
                targetSentences.append(sentence)
        sentences = targetSentences
        data = ''
        for s in sentences:
            data = data + '\n' + s
        if not isinstance(data, unicode):
            data = data.decode('utf-8')
        conn.execute("INSERT OR REPLACE INTO CORPUS(NAME, DATA)VALUES(?, ?)", [u_answer, data])
        conn.commit()
        
    conn.close()
    return sentences


def crawlBaiDu(answer):
    '''
    If the answer exist in the Resource.db, open the database.
    Else crawl BaiDu page of the answer, then save all the text into Resource.db.
    '''
    sentences = []
    u_answer = unicode(answer, 'utf-8')
    conn = sqlite3.connect('resources/Resource.db')
    try:    #access database
        cursor = conn.execute("SELECT * from BAIDU WHERE NAME=?", [u_answer])
        for r in cursor:
            for s in r[1].split('\n'):
                if len(s)>0:
                    sentences.append(s)
        sysPrint('Baidu db find '+ answer)
        conn.close()
    except: #crawl
        t0 = time.time()
        simple = Converter('zh-hans').convert(answer.decode('utf-8')).encode('utf-8')
        url="http://baike.baidu.com/search/word?word=" + simple
        html = urllib.urlopen(url)
        soup = BeautifulSoup(html, 'html.parser', from_encoding = 'utf-8')
        crawl_time = time.time()-t0
        sysPrint("crawl BaiDu time:  %0.3f" %crawl_time)
        
        comp = soup.getText()
        s = Converter('zh-hant').convert(comp)
        s = re.sub(r"\w", "", s)
        s = re.sub(ur".*瀏覽次數.*(\n.*)*|.*引用日期.*|.*詞條標簽.*", '', s)
        
        for line in s.split('\n'):
            if line != '' and checkChinese(line):
                line = line.replace(' ','').replace(u'（）', '').replace(u'[]', '')
                for s in line.split(u'。'):
                    sentences.append(s)
                    #print line
        #print type(sentences[0])
        ###insert to db###
        data = ''
        for s in sentences:
            data = data + '\n' + s
        conn.execute("INSERT INTO BAIDU(NAME, DATA)VALUES(?, ?)", [u_answer, data])
    return sentences

def checkFrequencyAndDistance(sentences, answer, keywordlist, cutWord = False, freqMethod = "sentence"):
    '''
    calculate Frequency: #(sentences that contain keyword)/#(all the sentences)
    calculate Average Distance: the average distance of answer and keyword among the sentences that contain both keyword and answer
    calculate Shortest Distance: the shortest distance of answer and keyword among the sentences that contain both keyword and answer
    '''
    double_count = 0 #number of sentence that contain both answer and keyword
    distance = [] #a list of distance between answer and keyword in the sentence that contain both of them 
    answer_length = len(answer)
    nkeyword = len(keywordlist) #number of keyword and its synonym

    for sentence in sentences:
        check = sentence
        if cutWord: #if the resource is corpus, it already have the sentence be cut into words
            check = sentence.split(' ')

        if answer in check:
            sentence = re.sub(r'\s', '', sentence)
            answer_position = -1
            keyword_position = -1
            tmp1 = -1
            tmp_dis = sys.maxint #tmp distance between answer and keyword
            while 1:
                tmp1 = sentence.find(answer, tmp1+1)
                if tmp1 == -1: #tmp position of answer
                    break
                for keyword in keywordlist:
                    tmp2 = -1 #tmp position of keyword
                    while 1:
                        #tmp2 = sentence.replace(answer, "0"*len(answer)).find(keyword, tmp2+1)
                        pattern = re.compile(keyword)
                        m=pattern.search(sentence.replace(answer," 0"*len(answer)),tmp2+1)
                        if not m:
                            break
                        tmp2=m.start()    

                        if tmp2 < tmp1:
                            if tmp1 - tmp2 < tmp_dis:
                                tmp_dis = tmp1 - tmp2
                                answer_position = tmp1
                                keyword_position = tmp2
                        else:   #because the answer has been remove, we have to add the length
                            if tmp2 - tmp1  < tmp_dis:
                                tmp_dis = tmp2 - tmp1 
                                answer_position = tmp1
                                keyword_position = tmp2 
            
            if tmp_dis < 30:
                distance.append(tmp_dis)
                double_count = double_count + 1
                #print sentence
                #print len(sentence)
            
            #print answer_position
            #print keyword_position
            #print distance[double_count]

    
    division = 0
    if freqMethod == "sentence":
        if len(sentences) > 0:
            division = double_count/float(len(sentences))
    else:
        kcount = 0 #number of sentence that contain keyword
        for sentence in sentences:
            if re.search('|'.join(keywordlist), sentence.replace(answer, "")) is not None:
                kcount += 1
        if len(sentences) > 0:
            division = kcount/float(len(sentences))
            #print kcount

    max_dist = 30
    average = 1
    shortest = 1
    if len(distance) > 0:
        average = sum(distance)/float(len(distance))
        average /= max_dist
        shortest = float(min(d for d in distance))
        shortest /= max_dist
        
    return {'frequency':division, 'distance_a':average, 'distance_s':shortest}



class AnswerData:
    def __init__(self,answer):
        self.answer=answer
        self.GoogleContent=crawlGoogle(answer)
        self.WikiContent=crawlWiki(answer)
        self.BaiDuContent=crawlBaiDu(answer)
        self.CorpusContent=crawlCorpus(answer)
        self.Content = self.GoogleContent
        self.Content.extend(self.WikiContent)
        self.Content.extend(self.BaiDuContent)
        self.Content.extend(self.CorpusContent)

    def matchPattern(self,text,pattern):
        for sentence in text:
            segments=re.compile(ur",|，|\.|。|!|！|\?|？|;|；").split(sentence) 
            for seg in segments:
                #sysPrint(seg)
                if re.search(pattern,seg) is not None:
                    sysPrint(seg)
                    return True
        return False 

    def findPattern(self,keywords):
        '''
        check if there are sentences matching patterns which contain answer and action keywords
        '''
        key_combination="|".join(keywords)
        pattern1="{0}.*?(可以|能|會)({1})".format(self.answer,key_combination).decode("utf-8") #(?!機)
        pattern2="{0}.*?({1})得.*?".format(self.answer,key_combination).decode("utf-8")
        sysPrint(pattern1)
        sysPrint(pattern2)

        text=self.Content #(unicode)
        result=self.matchPattern(text,pattern1)
        if result:
            return True
        result=self.matchPattern(text,pattern2)
        return result


    def findPatternWithObj(self,keywords,obj):
        '''
        check if there are sentences matching the pattern which contains answer, action keywords and object
        '''
        key_combination="|".join(keywords)
        pattern1="{0}.*?({1}).{{0,3}}{2}".format(self.answer,key_combination,obj).decode("utf-8")
        sysPrint(pattern1)

        text=self.Content #(unicode)
        result=self.matchPattern(text,pattern1) 
        return result
    
    def findPatternWithSbj(self,keywords,sbj):        
        '''
        check if there are sentences matching the pattern which contains answer, action keywords and subject
        '''
        key_combination="|".join(keywords)
        pattern1="{0}.*?({1}).{{0,3}}{2}".format(sbj,key_combination,self.answer).decode("utf-8") #木匠用鐵鎚 
        #or 鐵鎚是木匠用來..!?
        sysPrint(pattern1)

        text=self.Content #(unicode)
        result=self.matchPattern(text,pattern1) 
        return result 

    def getFeatures(self,keywordList,model_path):
        '''
        Input: 
            keywordList: a list containing keyword and its synnonym, 
            model_path: word embedding model

        Output:
            features extracted from answer-related content(Google,Wikipedia,Baidu,ASBC)
            in relation to keywords

            feature 0: ratio of co-occurrence frequency 
            feature 1: average distance between answer and keywords
            feature 2: shortest distance between answer and keywords
            feature 3: word vectors consine similarity between answer and keywords

        '''
        u_answer = unicode(self.answer, 'utf-8')
        #u_keyword = unicode(keyword, 'utf-8')
        u_keyword_lst=[unicode(k,'utf-8') for k in keywordList]

        check = checkFrequencyAndDistance(self.Content, u_answer, u_keyword_lst, False, "word")

        features=[]
        features.append(check['frequency'])
        features.append(check['distance_a'])
        features.append(check['distance_s'])
        

        global model
        if model is None:
            model = gensim.models.Word2Vec.load_word2vec_format(model_path, binary = True, unicode_errors = 'ignore')
            print 'model is None'

        similarity=0.1
        u_keyword=u_keyword_lst[0]
        if u_answer in model and u_keyword in model:
            similarity = model.similarity(u_answer, u_keyword)
        features.append(similarity)

        return features

if __name__ == '__main__':
    sys_type=sys.getfilesystemencoding()
    if len(sys.argv) == 3:
        answer = sys.argv[1].decode(sys_type).encode("utf-8")
        keyword = sys.argv[2].decode(sys_type).encode("utf-8")
        answer_data = AnswerData(answer)
        
        from ehownet import synonym
        synonym_words = synonym.synonym(keyword)
        examine_set = [s for s in synonym_words if s != keyword and  s in keyword]
        examine_set.insert(0, keyword)
        
        model_path="resources/cna_asbc_cbow_d300_w10_n10_hs0_i15.vectors.bin"
        features = answer_data.getFeatures(examine_set,model_path)
        print features
        
        import numpy as np
        features = np.array(features).reshape((1, -1))
        from sklearn.externals import joblib
        clf = joblib.load("resources/LinearSVC.pkl")
        scores = clf.decision_function(features)
        prob = 1. / (1. + np.exp(-scores))
        if len(prob.shape) == 1:
            _prob = np.vstack([1 - prob, prob]).T
        else:
            _prob = prob / prob.sum(axis=1).reshape((prob.shape[0], -1))
        max_ind = np.argmax(_prob)
        pred = clf.classes_[max_ind]
        scale_prob = (_prob[0,max_ind] - 0.5) * 1.6 + 0.1
        print "predict: ", pred
        print "prob: ", _prob[0,max_ind]
        print "scale_prob:", scale_prob
        
    else:
        print 'Usage:', sys.argv[0], '<answer> <keyword>'
