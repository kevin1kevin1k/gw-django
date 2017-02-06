#! python2
# -*- coding: UTF-8 -*-
import sys
import numpy as np
from sklearn.externals import joblib
import question_parser as qp
import main_process as mp
import crawl_wiki
import crawlData as cd
from ehownet import eh, synonym
import pickle
import time

def sysPrint(s):
    sys_type=sys.getfilesystemencoding()
    print (s.decode("utf-8").encode("mbcs"))

def predictByEhownet(answer,parsed_question,replaceU=False):
    result=[]
    qtype_lst=[]

    for i in range(len(parsed_question)):
        ans=answer[i]
        keyword_dict=parsed_question[i]

        #parse失敗..
        if len(keyword_dict)==0:
            sysPrint(str(i))
            result.append("?")
            continue


        for key in keyword_dict:
            for keyword in keyword_dict[key]:
                #sysPrint("type "+key)
                #sysPrint("keyword "+keyword)

                #有act時不單獨看
                if (key=="object" or key=="subject") and "act" in keyword_dict:
                    break
                
                qtype=key

                arg=dict()
                if key=="act":                    
                    if "object" in keyword_dict:
                        arg["object"]=keyword_dict["object"][0]
                        qtype="act+obj"
                    elif "subject" in keyword_dict:
                        arg["subject"]=keyword_dict["subject"][0]
                        qtype="act+sbj"
                arg[key]=keyword    
                ehownet_result,conf=eh.run(ans,arg)
                if replaceU and ehownet_result=="U":
                    ehownet_result="N"            
        result.append(ehownet_result)
        qtype_lst.append(qtype)

    return result,qtype_lst    


def predictByWiki(answer,parsed_question,replaceU=False):
    result=[]
    qtype_lst=[]
    wikidict = crawl_wiki.load_pkl_to_dict('resources/answer200.pkl')

    for i in range(len(parsed_question)):
        ans=answer[i]
        keyword_dict=parsed_question[i]

        if len(keyword_dict)==0:
            sysPrint(str(i))
            result.append("?")
            continue

        if replaceU:
            pre="N"
        else:
            pre="U"   

        for key in keyword_dict:
            for keyword in keyword_dict[key]:
                #有act時不單獨看
                if (key=="object" or key=="subject") and "act" in keyword_dict:
                    break

                qtype=key    

                if key=="act":                    
                    if "object" in keyword_dict:
                        keyword=keyword+keyword_dict["object"][0]
                        qtype="act+obj"
                    elif "subject" in keyword_dict:
                        keyword=keyword_dict["subject"][0]+keyword
                        qtype="act+sbj"
                if ans not in wikidict:
                    sysPrint(ans)
                    continue    
                word2depth = wikidict[ans]
                if keyword in word2depth:
                    depth = word2depth[keyword]
                    conf = 0.9 ** depth # 0.9 ** 7 < 0.5
                    if conf > 0.5:
                        pre="Y"
        result.append(pre)
        qtype_lst.append(qtype)
    return result,qtype_lst                            

def predictByPattern(answer,parsed_question,replaceU=False):
    result=[]
    qtype_lst=[]

    for i in range(len(parsed_question)):
        ans=answer[i]
        keyword_dict=parsed_question[i]

        if len(keyword_dict)==0:
            sysPrint(str(i))
            result.append("?")
            continue
        
        if replaceU:
            pred="N"
        else:
            pred="U"
        
        for key in keyword_dict:
            if key!="object" or key!="subject":
                qtype=key    

            if key!="act":
                continue

            for keyword in keyword_dict[key]:
                answer_data=cd.AnswerData(ans)

                #取得Keyword的同義詞 ex:穿戴 =>穿
                synonym_words=synonym.synonym(keyword)
                #examine_set=synonym_words
                examine_set=[s for s in synonym_words if s != keyword and  s in keyword]
                examine_set.insert(0, keyword)

                #Pattern Matching                
                if "object" in keyword_dict:
                    qtype="act+obj"
                    obj=keyword_dict["object"][0]
                    pattern_found=answer_data.findPatternWithObj(examine_set,obj)
                elif "subject" in keyword_dict:
                    qtype="act+sbj"
                    sbj=keyword_dict["subject"][0]
                    pattern_found=answer_data.findPatternWithSbj(examine_set,sbj)    
                else:
                    pattern_found=answer_data.findPattern(examine_set)
                
                if pattern_found:
                    pred="Y"
                else:
                    if replaceU:
                        pred="N"
                    else:
                        pred="U"
        result.append(pred)
        qtype_lst.append(qtype)                

    return result,qtype_lst

def predictProbaByClf(clf,X):
    scores = clf.decision_function(X)
    prob = 1. / (1. + np.exp(-scores))
    if len(prob.shape) == 1:
        return np.vstack([1 - prob, prob]).T
    else:
        return prob / prob.sum(axis=1).reshape((prob.shape[0], -1))

def predictByClassifier(answer,parsed_question):
    result=[]
    qtype_lst=[]
    clf = joblib.load("resources/LinearSVC.pkl")

    for i in range(len(parsed_question)):
        ans=answer[i]
        keyword_dict=parsed_question[i]

        if len(keyword_dict)==0:
            sysPrint(str(i))
            result.append("?")
            continue

        answer_data=cd.AnswerData(ans)

        for key in keyword_dict:    
            for keyword in keyword_dict[key]:
                #有act時不單獨看
                if (key=="object" or key=="subject") and "act" in keyword_dict:
                    break
                
                qtype=key

                #取得Keyword的同義詞 ex:穿戴 =>穿
                synonym_words=synonym.synonym(keyword)
                #examine_set=synonym_words
                examine_set=[s for s in synonym_words if s != keyword and  s in keyword]
                examine_set.insert(0, keyword)

                combine_set=examine_set
                if key=="act":
                    if "object" in keyword_dict:    
                        qtype="act+obj"
                        obj=keyword_dict["object"][0]
                        combine_set=["{0}.{{0,3}}{1}".format(s,obj) for s in examine_set]
                    elif "subject" in keyword_dict:
                        qtype="act+sbj"
                        sbj=keyword_dict["subject"][0]
                        combine_set=["{0}.*{1}".format(sbj,s) for s in examine_set]
                        
                #sysPrint("|".join(combine_set))
                features=answer_data.getFeatures(combine_set,model_path="resources/cna_asbc_cbow_d300_w10_n10_hs0_i15.vectors.bin")
                
                #if answer and keyword don't both appear in the text content, response no
                if features[0]==0:
                    print 'answer and keyword list do not both appear in the text content'
                    pred='N'
                    continue

                features=np.array(features).reshape((1, -1))
                prob=predictProbaByClf(clf,features)
                max_ind=np.argmax(prob)
                pred=clf.classes_[max_ind]
        result.append(pred)    
        qtype_lst.append(qtype)
    return result,qtype_lst        

def predictByAll(answer,parsed_question,replaceU=False,skip_component=""):
    #location,time,class,attr,act,object,subject,possession
    result=[]
    qtype_lst=[]   
    clf = joblib.load("resources/LinearSVC.pkl")
    wikidict = crawl_wiki.load_pkl_to_dict('resources/answer200.pkl')


    for i in range(len(parsed_question)):
        ans=answer[i]
        keywords_dict=parsed_question[i]

        if replaceU:
            pred="N"
        else:
            pred="U"

        for key in keywords_dict:
            for keyword in keywords_dict[key]:
                if (key=="object" or key=="subject") and "act" in keywords_dict:
                    break
                qtype=key

                if skip_component != 'Wiki':    
                    #看看是否可以從wiki找到答案
                    combine=keyword
                    if key=="act":                    
                        if "object" in keywords_dict:
                            combine=keyword+keywords_dict["object"][0]
                            qtype="act+obj"
                        if  "subject" in keywords_dict:
                            combine=keywords_dict["subject"][0]+keyword
                            qtype="act+sbj"

                    #print self.wikidict.keys()        
                    if ans in wikidict:
                        word2depth = wikidict[ans]
                        if combine in word2depth:
                            depth = word2depth[combine]
                            conf = 0.9 ** depth # 0.9 ** 7 < 0.5
                            if conf > 0.5:
                                pred="Y"
                                continue
                
                if skip_component != 'Ehownet':
                    #ehownet:
                    arg=dict()
                    if key=="act":                    
                        if "object" in keywords_dict:
                            arg["object"]=keywords_dict["object"][0]
                            qtype="act+obj"
                        if  "subject" in keywords_dict:
                            arg["subject"]=keywords_dict["subject"][0]
                            qtype="act+sbj"


                    arg[key]=keyword
                    ehownet_result,conf=eh.run(ans,arg)            

                    print ("ehownet:"+ehownet_result)
                    if ehownet_result != 'U':
                        pred=ehownet_result
                        continue

                ##other resource:
                
                ans_data=cd.AnswerData(ans)

                #取得Keyword的同義詞 ex:穿戴 =>穿
                synonym_words=synonym.synonym(keyword)
                #examine_set=synonym_words
                examine_set=[s for s in synonym_words if s != keyword and  s in keyword]
                examine_set.insert(0, keyword)

                if skip_component != 'Pattern':
                    #Pattern Matching
                    if key=="act":
                        start=time.clock()
                        
                        if "object" in keywords_dict:
                            obj=keywords_dict["object"][0]
                            qtype="act+obj"
                            pattern_found=ans_data.findPatternWithObj(examine_set,obj)
                        elif "subject" in keywords_dict:
                            sbj=keywords_dict["subject"][0]
                            qtype="act+sbj"
                            pattern_found=ans_data.findPatternWithSbj(examine_set,sbj)    
                        else:
                            pattern_found=ans_data.findPattern(examine_set)

                        end = time.clock()
                        print "Pattern matching time consuming: ",end - start

                        if pattern_found:
                            pred="Y"
                            continue
                
                if skip_component != 'Clf':
                    #classifier
                    start=time.clock()
                    combine_set=examine_set
                    if key=="act":
                        if "object" in keywords_dict:    
                            obj=keywords_dict["object"][0]
                            combine_set=["{0}.{{0,3}}{1}".format(s,obj) for s in examine_set]
                            qtype="act+obj"
                        elif "subject" in keywords_dict:
                            sbj=keywords_dict["subject"][0]
                            combine_set=["{0}.*{1}".format(sbj,s) for s in examine_set]
                            qtype="act+sbj"
                            
                                
                    sysPrint("|".join(combine_set))
                    features=ans_data.getFeatures(combine_set,model_path="resources/cna_asbc_cbow_d300_w10_n10_hs0_i15.vectors.bin")
                    print features
                    end = time.clock()
                    print "feature extraction time consuming: ",end - start
                    
                    #if answer and keyword don't both appear in the text content, response no
                    if features[0]==0:
                        print 'answer and keyword list do not both appear in the text content'
                        pred='N'
                        continue

                    start = time.clock()
                    features=np.array(features).reshape((1, -1))
                    prob=predictProbaByClf(clf,features)
                    max_ind=np.argmax(prob)
                    
                    pred=clf.classes_[max_ind]
                    
                    end = time.clock()
                    scale_prob = (prob[0,max_ind] - 0.5) * 1.6 + 0.1
                    print "prediction time consuming: ",end - start

        result.append(pred)    
        qtype_lst.append(qtype)
    return result,qtype_lst             
    

key_lst=["class","attr","act","act+obj","act+sbj","location"]
def analyze(pred,label,qtype):
    score=[1 if pred[i]==label[i] else 0 for i in range(len(pred))]
    #        class attr act act+obj act+sbj location total
    #Y
    #U
    #N
    #total
    confusion_matrix_t=[]
    for key in key_lst:
        type_score=[score[i] for i in range(len(score)) if qtype[i]==key]
        type_result=[pred[i] for i in range(len(pred)) if qtype[i]==key]
        
        total=len(type_score)
        YN=sum(type_score)
        UN=type_result.count("U")
        NN=total-YN-UN
        confusion_matrix_t.append([str(YN),str(UN),str(NN),str(total)])

    total=len(score)
    total_YN=sum(score)
    total_UN=pred.count("U")
    total_NN=total-total_YN-total_UN
    confusion_matrix_t.append([str(total_YN),str(total_UN),str(total_NN),str(total)])

    cmt_ac = np.array(confusion_matrix_t)
    return cmt_ac.T #transpose

def outputToFile(cm,fpath,title):
    output=open(fpath,"a")

    output.write(title+"\n")
    
    head=[""]+key_lst+["total"]
    output.write(",".join(head)+"\n")

    output.write("答對    , {0}\n".format(", ".join(cm[0])))
    output.write("不確定  , {0}\n".format(", ".join(cm[1])))
    output.write("答錯    , {0}\n".format(", ".join(cm[2])))
    output.write("Total,{0}\n".format(",".join(cm[3])))

    output.close()

def logError(answer,question,label,pred,title,fPath):
    indicator=[1 if pred[i]==label[i] else 0 for i in range(len(pred))]

    temp="Predict:{0}, Label:{1}, {2}, {3}"
    wrong=[temp.format(pred[i],label[i],answer[i],question[i]) for i in range(len(indicator)) if not indicator[i]]
    accurate=[temp.format(pred[i],label[i],answer[i],question[i]) for i in range(len(indicator)) if indicator[i]]
    log=open(fPath,"a")
    log.write(title+"\n")
    log.write("\n".join(wrong))
    log.write("\n")
    log.write("\n".join(accurate))
    log.write("\n")
    log.close()

def predictByAllDetail():
    data=qp.getQuestionList("Temp/testing_data_extend.txt")
    # data=qp.getQuestionList("Temp/ttt.txt")
    question=data["question"]
    answer=data["answer"]
    label=data["lable"]
    result=[]

    responder = mp.Responder()

    for i in range(len(question)):
        result.append(responder.process(answer[i],question[i])[0])

    source = [r.source for r in result]
    unique_source= set(source)
    source_statistics=[]
    for s in unique_source:
        scount = source.count(s)
        acc_count=0
        for i, r in enumerate(result):
            if r.source == s:
                pred = r.label
                truth = label[i]

                if pred==truth:
                    acc_count+=1

        source_statistics.append("{}\t{}\t{}\t{}".format(s,acc_count,scount-acc_count,scount))

    output=open("Temp/all.txt","a")
    output.write("\nSource\taccurate\twrong\ttotal\n")
    output.write("\n".join(source_statistics))
    output.close()

def main():
    #data=qp.getQuestionList("Temp/ttt.txt")
    data=qp.getQuestionList("Temp/testing_data_extend.txt")
    question=data["question"]
    answer=data["answer"]
    label=data["lable"]
    
    parser=qp.question_parser()
    parsed_result=[]
    
    fh = open("Temp/parsed_testing_question.bin", 'rb')
    parsed_result = pickle.load(fh)
    
    # for q in question:
    #     keyword_dict,nq=parser.parse_question(q)
    #     parsed_result.append(keyword_dict)

    #     if len(keyword_dict)==0:
    #         sysPrint(q)

    # fh = open("Temp/parsed_testing_question.bin", 'wb')
    # pickle.dump(parsed_result, fh)        
    
    sysPrint("----Parse Quetsion OK----")


    start=time.clock()    
    all_pred,all_qtype=predictByAll(answer,parsed_result,replaceU=False,skip_component="")
    end=time.clock()    
    sysPrint("----All Process Prediction OK {0} s----".format(end-start))


    # start=time.clock()    
    # eh_pred,eh_qtype=predictByEhownet(answer,parsed_result)
    # end=time.clock()    
    # sysPrint("----Ehownet Prediction OK : {0} s----".format(end-start))
    
    # start=time.clock()    
    # wiki_pred,wiki_qtype=predictByWiki(answer,parsed_result)
    # end=time.clock()    
    # sysPrint("----Wiki Prediction OK {0} s----".format(end-start))
    
    # start=time.clock()    
    # pt_pred,pt_qtype=predictByPattern(answer,parsed_result)
    # end=time.clock()    
    # sysPrint("----Pattern Prediction  OK {0} s----".format(end-start))
    
    # start=time.clock()    
    # clf_pred,clf_qtype=predictByClassifier(answer,parsed_result)
    # end=time.clock()    
    # sysPrint("----Classifier Prediction OK {0} s----".format(end-start))

    outputFile="Temp/evaluation_ablation.txt"
    # logErrorFile="Temp/predict_error.txt"

    # eh_cm=analyze(eh_pred,label,eh_qtype)
    # outputToFile(eh_cm,outputFile,"EHownet")    
    # logError(answer,question,label,eh_pred,"EHownet",logErrorFile)

    # wiki_cm=analyze(wiki_pred,label,wiki_qtype)
    # outputToFile(wiki_cm,outputFile,"Wiki")
    # logError(answer,question,label,wiki_pred,"Wiki",logErrorFile)
    
    # pt_cm=analyze(pt_pred,label,pt_qtype)
    # outputToFile(pt_cm,outputFile,"Pattern")
    # logError(answer,question,label,pt_pred,"Pattern",logErrorFile)
    
    # clf_cm=analyze(clf_pred,label,clf_qtype)
    # outputToFile(clf_cm,outputFile,"Classifier")
    # logError(answer,question,label,clf_pred,"Classifier",logErrorFile)

    all_cm=analyze(all_pred,label,all_qtype)
    outputToFile(all_cm,outputFile,"All process")
    # logError(answer,question,label,all_pred,"All process",logErrorFile)

if __name__ == '__main__':
    main()
    # predictByAllDetail()
