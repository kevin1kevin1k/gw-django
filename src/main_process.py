#! python2
# coding: utf-8

import sys
import numpy as np
from sklearn.externals import joblib
from sklearn.svm import LinearSVC
import crawlData as cd
import question_parser as qs
import time
from ehownet import eh, synonym,ancestors
import re
from collections import namedtuple
import crawl_wiki

def sysPrint(s):    
    
    sys_type=sys.getfilesystemencoding()
    print s.decode("utf-8").encode(sys_type)

class Responder():
    def __init__(self,ehownetPath="ehownet_word.txt",model_path="cna_asbc_cbow_d300_w10_n10_hs0_i15.vectors.bin",clf_path="LinearSVC.pkl"):
        cd.load(model_path)
        self.parser=qs.question_parser(ehownetPath)
        self.model_path=model_path
        self.clf = joblib.load(clf_path)
        self.answer_data=None
        self.wikidict = crawl_wiki.load_pkl_to_dict('answer200.pkl')

        self.has_updated = False

    def predictProbaByClf(self,clf,X):
        scores = clf.decision_function(X)
        prob = 1. / (1. + np.exp(-scores))
        if len(prob.shape) == 1:
            return np.vstack([1 - prob, prob]).T
        else:
            return prob / prob.sum(axis=1).reshape((prob.shape[0], -1))

    def responseSentence(self,ques, ls):
        res_ls = []
        if len(ls) == 1:
            res = ques.replace('嗎', '')
            if ls[0][1] == 'N':
                if re.search('是', ques):
                    res = res.replace('是', '不是')
                elif re.search('可以', ques):
                    res = res.replace('可以', '不可以')
                elif re.search('會', ques):
                    res = res.replace('會', '不會')
                elif re.search('有',ques):
                    res=res.replace('有','沒有')
                elif re.search('需要', ques):
                    res = res.replace('需要', '不需要')
                elif re.search('能', ques):
                    res = res.replace('能', '不能')
                elif re.search('要', ques):
                    res = res.replace('要', '不需要')
                elif re.search('有關', ques):
                    res = res.replace('有關', '無關')
                elif re.search('得到', ques):
                    res = res.replace('得到', '不到')
                else:
                    res = res.replace('它', '它不')
                    res = res.replace('他', '他不')

            res_ls.append(res)
        else:
            for term in ls:
                if term[2] == 'act':
                    if re.search('可以|能', ques):
                        helper = '可以'
                    else:
                        helper = '會'
                    if term[1] == 'Y':
                        res = '它' + helper + term[0]
                    else:
                        res = '它不' + helper + term[0]
                elif term[2] == 'attr':
                    if term[1] == 'Y':
                        res = '它是' + term[0] + '的'
                    else:
                        res = '它不是' + term[0] + '的'
                else:
                    if term[1] == 'Y':
                        res = '它是' + term[0]
                    else:
                        res = '它不是' + term[0]
                res_ls.append(res)
        return res_ls

    def process(self,answer,question,update_data=True):
        self.has_updated = False
        
        Response = namedtuple('Response', ["keyword","qtype","label","conf","source","answer_str","new_question","is_neg"])
        ## parse the question
        keywords_dict,new_question=self.parser.parse_question(question)
        is_neg=self.parser.isNegativeSentence(question)

        if len(keywords_dict)==0:
            #print "不能理解此問題"
            return [Response(keyword="",qtype="",label="?",conf="",source="Parser",answer_str="不能理解此問題",
                new_question="",is_neg=False)]
        
        #檢查是否答對
        ans_syns = synonym.synonym(answer)
        
        #start = time.clock()
        kwds = [kwd for keys in keywords_dict.values() for kwd in keys]
        success = len(set(ans_syns) & set(kwds)) > 0 or \
                any([ancestors.belong(kwd, answer) for kwd in kwds])
        if success:
            sysPrint("AC!")
            return [Response(keyword="",qtype="",label="AC",conf="",source="",answer_str="",
                new_question="",is_neg=False)]

        #檢查問題是否包含它
        if re.search("它|他|她|牠",new_question) is None:
            sysPrint("illegal")
            return [Response(keyword="",qtype="",label="illegal",conf="",source="",answer_str="",
                new_question="",is_neg=False)]                

        #location,time,class,attr,act,object,subject,possession
        answer_lst=[]    
        for key in keywords_dict:
            for keyword in keywords_dict[key]:
                sysPrint("type "+key)
                sysPrint("keyword "+keyword)

                #有act時不單獨看
                if (key=="object" or key=="subject") and "act" in keywords_dict:
                    break
                                
                #看看是否可以從wiki找到答案
                if key=="act":                    
                    if "object" in keywords_dict:
                        keyword=keyword+keywords_dict["object"][0]
                    if     "subject" in keywords_dict:
                        keyword=keywords_dict["subject"][0]+keyword

                #print self.wikidict.keys()        
                if answer in self.wikidict:
                    word2depth = self.wikidict[answer]
                    if keyword in word2depth:
                        depth = word2depth[keyword]
                        conf = 0.9 ** depth # 0.9 ** 7 < 0.5
                        if conf > 0.5:
                            answer_lst.append( (keyword, key, 'Y', 'Wiki', str(conf)) )
                            continue
                
                #ehownet:
                arg=dict()
                if key=="act":                    
                    if "object" in keywords_dict:
                        arg["object"]=keywords_dict["object"][0]
                    if     "subject" in keywords_dict:
                        arg["subject"]=keywords_dict["subject"][0]
    
                arg[key]=keyword
                ehownet_result,conf=eh.run(answer,arg)            

                # ehownet_result="U"
                # conf=0.1

                print "ehownet:",ehownet_result
                if ehownet_result != 'U':
                    answer_lst.append((keyword,key,ehownet_result,"Ehownet",str(conf)))
                    continue

                ##other resource:
                
                if update_data or self.answer_data is None:
                    start = time.clock()

                    self.answer_data=cd.AnswerData(answer)
                    self.has_updated = True

                    end = time.clock()            
                    print "update data time consuming: ",end - start    

                #取得Keyword的同義詞 ex:穿戴 =>穿
                synonym_words=synonym.synonym(keyword)
                #examine_set=synonym_words
                examine_set=[s for s in synonym_words if s != keyword and  s in keyword]
                examine_set.insert(0, keyword)

                #Pattern Matching
                if key=="act":
                    start=time.clock()
                    
                    if "object" in keywords_dict:
                        obj=keywords_dict["object"][0]
                        pattern_found=self.answer_data.findPatternWithObj(examine_set,obj)
                    elif "subject" in keywords_dict:
                        sbj=keywords_dict["subject"][0]
                        pattern_found=self.answer_data.findPatternWithSbj(examine_set,sbj)    
                    else:
                        pattern_found=self.answer_data.findPattern(examine_set)

                    end = time.clock()
                    print "Pattern matching time consuming: ",end - start

                    if pattern_found:
                        answer_lst.append((keyword,key,"Y","Pattern","1"))
                        continue

                #classifier
                start=time.clock()
                combine_set=examine_set
                if key=="act":
                    if "object" in keywords_dict:    
                        obj=keywords_dict["object"][0]
                        combine_set=["{0}.{{0,3}}{1}".format(s,obj) for s in examine_set]
                    elif "subject" in keywords_dict:
                        sbj=keywords_dict["subject"][0]
                        combine_set=["{0}.*{1}".format(sbj,s) for s in examine_set]
                        
                            
                sysPrint("|".join(combine_set))
                features=self.answer_data.getFeatures(combine_set,self.model_path)
                print features
                end = time.clock()
                print "feature extraction time consuming: ",end - start

                start = time.clock()
                features=np.array(features).reshape((1, -1))
                prob=self.predictProbaByClf(self.clf,features)
                max_ind=np.argmax(prob)
                pred=self.clf.classes_[max_ind]
                end = time.clock()
                print "prediction time consuming: ",end - start
                answer_lst.append((keyword,key, pred,"Model",str(prob[0,max_ind])))

        temp=[(item[0],item[2],item[1]) for item in answer_lst ]
        answer_sentence=self.responseSentence(new_question,temp)
        
        result=[]
        for i in range(len(answer_lst)):
            ans=answer_lst[i]
            ans_str=answer_sentence[i]
            r=Response(keyword=ans[0],qtype=ans[1],label=ans[2],source=ans[3],conf=ans[4],answer_str=ans_str,
                new_question=new_question,is_neg=is_neg)
            result.append(r)
        return result

    
def main():
    sys_type=sys.getfilesystemencoding()
    #responder = Responder(ehownetPath="ehownet_word.txt",model_path="cna_asbc_cbow_d300_w10_n10_hs0_i15.vectors.bin",clf_path="LogisticRegression.pkl")
    responder = Responder(ehownetPath="ehownet_word.txt",model_path="cna_asbc_cbow_d300_w10_n10_hs0_i15.vectors.bin",clf_path="LinearSVC.pkl")
    pre_answer=""
    while True:
        hello=u"請輸入答案 問題\n"
        input_s=raw_input(hello.encode(sys_type))
        seg=input_s.split(" ")
        if len(seg)<2:
            continue
        answer=seg[0].decode(sys_type).encode("utf-8")
        question=seg[1].decode(sys_type).encode("utf-8")
        if answer!=pre_answer:
            update = True
            pre_answer=answer
        responses=responder.process(answer,question,update)
        if responder.has_updated:
            update = False

        for res in responses: 
            sysPrint("{r.keyword}, {r.label}, {r.conf}, {r.qtype}, {r.source}\n{r.answer_str}\n".format(r=res))

    
if __name__ == '__main__':
    main()        
            
