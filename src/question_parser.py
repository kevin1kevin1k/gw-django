#! python2
# -*- coding:utf-8 -*-
import string_parser as sp
import CKIPParserClient as cc
import re
from ehownet import ancestors

def winPrint(s):
    if __name__ == '__main__':        
        import sys
        sys_type=sys.getfilesystemencoding()
        print s.decode("utf-8").encode(sys_type)
                
def segmentSentence(s):
    parse_str = question_parser.call_ckipparser_server(s)
    root= sp.create_tree(parse_str)
    segments=sp.getAllLeafNodes(root)
    return segments

class question_parser:
    def __init__(self, ehownetPath = "resources/ehownet_word.txt"):
        # ancestors.load()
        self.stopWordLst=set(["它","在","是","的","有","跟","和","有的","有關","拿來","裡",
            "東西","一種","某種","做","他","她","牠","祂","功能","或","屬於","類型",
            "需要","用到","一個","含","做出來","無關"])
        self.eNouns=set()
        with open(ehownetPath,"r") as file:
            for line in file.readlines():
                seg=line.rstrip()
                self.eNouns.add(seg)

    """
        question must be a string with utf-8 encoding
    """
    @staticmethod
    def call_ckipparser(s):

        result=''

        ps_path="C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"

        import os
        dir_path=os.path.dirname(os.path.abspath(__file__))

        script_path=os.path.join(dir_path,"parse.ps1")
        input_file=os.path.join(dir_path,"temp_question.txt")
        output_file=os.path.join(dir_path,"temp_question_parse.txt")

        with open(input_file,'w') as output:
            output.write(s.decode("utf-8").encode("big5"))
        import subprocess 
        command=[ps_path,script_path,input_file,output_file]
        try:
            subprocess.check_call(command)
            with open(output_file,'r') as parse_result:
                line = parse_result.readline()
                #print line.decode("utf-8").encode('mbcs')
            import re
            result=line.replace("#","")
            result=re.sub(r"\d+:\d+.\[\d\] ","",line)

        except Exception as e:
            print str(e)    

        return result


    """
        question must be a string with utf-8 encoding
    """
    @staticmethod
    def call_ckipparser_server(s):

        #解析器的參數
        options={}
        options['divide']=300
        options['encoding']="UTF-8"
        #options['encoding']="Big5"
        #options['pos']=True
        options['pos']=False
        options['server']='140.109.19.130'
        #options['port']=1501
        options['port']=8002
        options['xml']=False

        input_file="temp_question.txt"
        output_file="temp_question_parse.txt"
        uwfile=None

        #將要解析的句子寫入檔案
        with open(input_file,'w') as output:
            output.write(s.decode("utf-8").encode("big5"))

        #呼叫CKIP server 進行解析
        srv = cc.CkipSrv("ckip","ckip",server=options['server'], port=options['port'])
        srv.segFile(input_file, output_file, uwfile, options)

        #讀取解析結果
        with open(output_file,'r') as parse_result:
                line = parse_result.readline()
                #print line.decode("utf-8").encode('mbcs')
        import re
        line=line.decode("big5").encode("utf-8")
        result=line.replace("#","")
        result=re.sub(r"\d+:\d+.\[\d\] ","",result)
        result=re.sub(r"\s","",result)

        return result

    # def getEHowNetNouns(path):
    #     eNouns=set()
    #     with open(path,"r") as file:
    #         for line in file.readlines():
    #             seg=line.split("\t")
    #             #winPrint(seg[1])
    #             eNouns.add(seg[1])
    #     return eNouns

    @staticmethod
    def isNegativeSentence(s):
        s = s.decode('utf-8')
        m=re.search(ur"[^會]不會|[^是]不是|[^有]沒有|[^能]不能|[^可]不可以|[^需]不需要|[^有]無關|不用|它不",s)
        return m is not None

    def getWord(self,s):
        word=""
        segments=s.split(":")
        if len(segments)>=3:
            word=segments[2]
        return word

    def getPOS(self,s):
        pos=""
        segments=s.split(":")
        if len(segments)>=2:
            pos=segments[1]
        return pos

    def getUniqList(self,input):
        output=[]
        for x in input:
            if x not in output and x != "":
                output.append(x)
        return output

    def isStopWord(self,word):
        return word in self.stopWordLst

    def _processQuestionBySpecificRule(self,question):
        question=question.replace("的一種","")
        question=question.replace("每天都","每天")
        question=question.replace("一種菜","一種蔬菜")
        question=question.replace("該不會","")
        return question

    def processQuestionBySpecificRule(self,question,root):

        question=self._processQuestionBySpecificRule(question)

        #換成肯定句
        question=question.decode("utf-8")

        if re.search(ur"是?不是",question):
            question=re.sub(ur"是?不是",u"是",question)
        elif re.search(ur"會?不會",question) :
            question=re.sub(ur"會?不會",u"會",question)
        elif re.search(ur"有?沒有",question):
            question=re.sub(ur"有?沒有",u"有",question)
        elif re.search(ur"能?不能",question):
            question=re.sub(ur"能?不能",u"能",question)
        elif re.search(ur"可?不可以",question):
            question=re.sub(ur"可?不可以",u"可以",question)
        elif re.search(ur"需?不需要",question):
            question=re.sub(ur"需?不需要",u"需要",question)
        elif re.search(ur"有?無關",question):
            question=re.sub(ur"有?無關",u"有關",question)
        elif re.search(ur"不用",question):
            question=re.sub(ur"不用",u"要",question)
        else:            
            neg=sp.getTargetNode(root,"negation:")
            if neg:
                segments=neg.data.split(":")
                if len(segments)>=3:
                    neg_word=segments[2]
                    question=question.replace(neg_word.decode('utf-8'),u"")
        question=question.encode("utf-8")                                

        return question

    def judge_qtype(self,question):    
        #句型判斷    
        qtype="u"
        if re.search("是|屬於",question) is not None:
            qtype="c"    
            # if re.search("屬於|屬于|歸屬|一種|某種",question) is not None:
            #     qtype="cc"
        if re.search("的嗎|有關",question) is  not None:
            qtype="a" 

        return qtype        
    def add_to_dict(self,target_dict,key,item):
        if key in target_dict:
            target_dict[key].append(item)
        else:
            target_dict[key]=[item]

    def arrange_dict(self,key_dict):
        if "object" in key_dict and "act" not in key_dict:
            for kw in key_dict["object"]:
                self.add_to_dict(key_dict,"attr",kw)
            key_dict.pop('object', None)    

        if "subject" in key_dict and "act" not in key_dict:
            for kw in key_dict["subject"]:
                self.add_to_dict(key_dict,"attr",kw)
            key_dict.pop('subject', None)    

    def find_property_head(self,node,qtype,key_dict):
        pp=""
        quan_head=""
        headList=[]

        #不要重複判斷
        toRemove=[]    
        for key in key_dict:
            for item in key_dict[key]:
                toRemove.append(item)

        #找property
        p_node=sp.getTargetNode(node,"property|apposition:|predication")
        if p_node is not None:
            if len(p_node.child)==0: ##this is a leaf node ,get data directly
                word=self.getWord(p_node.data)
                winPrint(word)
                pp=word
            else: ##find the head
                head_node=sp.getTargetLeafNode(p_node,"property:|head:|Head:(?!Ng|DE)")
                if head_node is not None:
                    word=self.getWord(head_node.data)
                    winPrint(word)
                    pp=word

        #找量詞
        quan_node=sp.getTargetNode(node,"quantifier:DM")
        if quan_node is not None:
            quan=self.getWord(quan_node.data)
            quan_parent_node=sp.getTargetParentNode(node,ur"quantifier:DM")
            if quan_parent_node is not None:
                head_node=sp.getTargetLeafNode(quan_parent_node,"Head")
                if head_node is not None:
                    word=self.getWord(head_node.data)
                    if not self.isStopWord(quan) and not self.isStopWord(word):
                        quan_head=quan+word
                        self.add_to_dict(key_dict,"attr",quan_head)
                        toRemove.append(word)
                        toRemove.append(quan)
                        winPrint(quan_head)


        #找Head
        head_node_lst=sp.getAllTargetLeafNode(node,r"Head:(?!Ncda|Ncdb|P|Ng)|DM:",[])

        ##重新安排順序: 名詞, 動詞反轉
        head_node_lst=list(reversed(head_node_lst)) #反轉 後面的可能比較重要
        noun_node_lst=[n for n in head_node_lst if ":N" in n.data]
        rn_lst=[n for n in head_node_lst if n not in noun_node_lst]
        head_node_lst=noun_node_lst+rn_lst

        if len(head_node_lst) >0:
            for head_node in head_node_lst:
                word=self.getWord(head_node.data)
                pos=self.getPOS(head_node.data)
                winPrint(word)
                headList.append((word,pos))    

        #找找看是否可以組合成一個詞
        combine_success=False
        combine_lst=[]    
        if pp and len(head_node_lst)>0:
            for head_pos in headList:
                head=head_pos[0]
                pos=head_pos[1]
                if not head or "V" in pos or head in toRemove: #通常是property+名詞的組合
                    continue 
                combine=pp+head
                if combine in self.eNouns:
                    combine_success=True

                    combine_lst.append((combine,"N"))
                    toRemove.append(head)

        headList=combine_lst+headList #串在一起後面再一起判斷
                        
        if pp and combine_success==False and pp not in toRemove and not self.isStopWord(pp):
            #放在property的應該是attr 或  act
            if ancestors.is_act(pp):
                self.add_to_dict(key_dict,"act",pp)    
            else:
                self.add_to_dict(key_dict,"attr",pp)

            toRemove.append(pp)    #不要重複放

        for head_pos in headList:
            head=head_pos[0]
            pos=head_pos[1]
            if head not in toRemove and not self.isStopWord(head):
                    word_type=ancestors.get_type(head)        
                    if qtype=="c" and word_type=="class" and not ancestors.is_attr(head):
                        self.add_to_dict(key_dict,"class",head)    
                    elif (qtype=="a" and "subject" not in key_dict) or word_type=="attr":
                        self.add_to_dict(key_dict,"attr",head)
                    #elif word_type=="act" and "V" in pos:
                    elif "V" in pos:
                        self.add_to_dict(key_dict,"act",head)
                    elif word_type=="class" or "N" in pos:
                        self.add_to_dict(key_dict,"object",head)                    
                    else:
                        self.add_to_dict(key_dict,word_type,head)    


    def parse_question(self,question):
        #key_dict={"act":"","attr":"","class":"","time":"","location":"","object":"","possession":""}            
        key_dict={}

        #analyze question type : class or attribute?
        qtype= self.judge_qtype(question)
        winPrint(qtype)

        parse_str = self.call_ckipparser_server(question)
        winPrint(parse_str)

        root= sp.create_tree(parse_str)

        #process question string
        question=self.processQuestionBySpecificRule(question,root)
        winPrint(question)


        try:    
            
            #如果只有一個名詞片語,直接回傳
            if root.data=="NP":
                self.add_to_dict(key_dict,"class",question)
                question="它是"+question
                return key_dict,question
            #用rule去取keyword

            ##rule 1 : 取location(NP中的名詞) 和 time 
            #拿到location就return
            if "location" in parse_str :
                location_node=sp.getTargetNode(root,"location")
                if location_node is not None:
                    n_node=sp.getTargetLeafNode(location_node,":Na|:Ncb|:Nca|:Dg")
                    if n_node is not None:
                        word=self.getWord(n_node.data)
                        winPrint(word)
                        self.add_to_dict(key_dict,"location",word)
                        return key_dict,question    

            elif re.search(":Nca|:Ncb|:Ncc|:Nce",parse_str) is not None:
                node=sp.getTargetLeafNode(root,":Nca|:Ncb|:Ncc|:Nce")
                if node is not None:
                    word=self.getWord(node.data)
                    winPrint(word)
                    self.add_to_dict(key_dict,"location",word)
                    return key_dict,question    

            #取時間
            #拿到就return
            if "time" in parse_str:
                time_node=sp.getTargetNode(root,"time")
                if time_node is not None:
                    n_node=sp.getTargetLeafNode(time_node,"Head:(?!Ng|Nhaa|P)|Dd:|DM:")    
                    if n_node is not None:
                        word=self.getWord(n_node.data)
                        winPrint(word)
                        self.add_to_dict(key_dict,"time",word)
                        return key_dict    ,question
            
            ##找所有格
            possession_node=sp.getTargetParentNode(root,ur"N.的")
            if possession_node is not None and sp.getTargetLeafNode(possession_node,r"它|他|他") :
                head_node=sp.getTargetLeafNode(possession_node,"Head:(?!Ng|DE)")
                if head_node is not None:
                    word=self.getWord(head_node.data)
                    if not self.isStopWord(word):
                        winPrint(word)
                        self.add_to_dict(key_dict,"possession",word)

            
            #找動詞的agent
            agent_node=sp.getTargetNode(root,"agent:")
            if agent_node is not None:
                head_node=sp.getTargetLeafNode(agent_node,"Head:[^P]")
                if head_node is not None:
                    word=self.getWord(head_node.data)
                    if not self.isStopWord(word):
                        self.add_to_dict(key_dict,"subject",word)
                        winPrint(word)             

            ##rule 2 : a是b, 取b
            if "V_11:是" in parse_str:
                #print "rule 2"
                range_node =sp.getTargetNode(root,"range:|complement:|particle:S")
                if range_node is not None:
                    #找property和head和其可能的組合
                    self.find_property_head(range_node,qtype,key_dict)

                    # for item in range_dict:
                    #     key_dict[item]=range_dict[item]

            ##rule 3 一般動詞:             
            else:
                head_node= sp.getTargetNode(root,"Head",method="bfs")
                if head_node is not None and len(head_node.child)>0:
                    head_node= sp.getTargetLeafNode(head_node,"Head")

                if head_node is not None:
                    #取Head 通常是動詞
                    word=self.getWord(head_node.data)
                    if word and not self.isStopWord(word):
                        if ancestors.is_act(word) and "V" in head_node.data:
                            self.add_to_dict(key_dict,"act",word)
                        elif ancestors.is_attr(word):
                            self.add_to_dict(key_dict,"attr",word)

                    ###判斷動詞類別
                    verb=head_node.data.split(":")[1]
                    match_obj=re.search(r"V[BCFIJGK]|V_2|S",verb)

                    ###及物動詞,分類動詞等等要再取受詞
                    if match_obj is not None:
                        range_node =sp.getTargetNode(root,r"range:|goal:|companion:|particle:S|condition:|property:|comparison:",method="bfs")
                        if range_node is not None:
                            #找property和head和其可能的組合
                            self.find_property_head(range_node,qtype,key_dict)        
                            
                        else :
                            comple_node =sp.getTargetNode(root,"complement:")
                            existed=[]
                            for lst in key_dict.values():
                                existed.extend(lst)

                            if comple_node is not None:
                                if len(comple_node.child)==0:
                                    word=self.getWord(comple_node.data)
                                    if word not in existed and not self.isStopWord(word): #還沒取過
                                        word_type=ancestors.get_type(word)
                                        self.add_to_dict(key_dict,word_type,word)
                                        winPrint(word)
                                else :
                                    head_node=sp.getTargetLeafNode(comple_node,"Head:")
                                    if head_node is not None:
                                        word=self.getWord(head_node.data)
                                        if word not in existed and not self.isStopWord(word): #還沒取過
                                            word_type=ancestors.get_type(word)
                                            self.add_to_dict(key_dict,word_type,word)
                                            winPrint(word)

                        #因為theme通常比range,goal不重要,擺在後面才加進list        
                        #theme_node =sp.getTargetNode(root,r"theme:\w+\(Head:(?!Nhaa)|condition")
                        theme_node =sp.getTargetNodeExcept(root,r"theme:",r"Nhaa")
                        existed=[]
                        for lst in key_dict.values():
                            existed.extend(lst)
                        if theme_node is not None:
                            #n_node=sp.getTargetLeafNode(theme_node,"Head:[^P]|DUMMY")
                            head_node_lst=sp.getAllTargetLeafNode(theme_node,"Head:[^P]|DUMMY",[])
                            for head in head_node_lst:
                                word=self.getWord(head.data)
                                pos = self.getPOS(head.data)
                                if word not in existed and not self.isStopWord(word): #還沒取過                                
                                    word_type=ancestors.get_type(word)
                                    if qtype=="a":
                                        self.add_to_dict(key_dict,"attr",word)
                                    elif word_type=="class" or "N" in pos:
                                        self.add_to_dict(key_dict,"object",word)
                                    else:    
                                        self.add_to_dict(key_dict,word_type,word)
                                    winPrint(word)

        except Exception as e:
            print str(e)
            #keyword.append("error")

        self.arrange_dict(key_dict)    
        winPrint("\n\n")
        for key in key_dict:
            winPrint( key)
            winPrint(" ".join(key_dict[key]))

        return key_dict,question

def getQuestionList(fpath):
    ans=[]
    question=[]
    lable=[]
    with open(fpath,"r") as file:
        for line in file.readlines():
            line=line.strip()
            winPrint(line)
            #print line.decode("utf-8").encode("mbcs")
            segments=line.split(",")
            ans.append(segments[0])
            question.append(segments[1])
            lable.append(segments[2])
            #lable.append(segments[2][0])
    return {"answer":ans,"question":question,"lable":lable}        


if __name__ == '__main__':
    import sys
    sys_type=sys.getfilesystemencoding()
    ehownetPath="resources/ehownet_word.txt"
    #eNouns=getEHowNetNouns(ehownetPath)    
    parser=question_parser(ehownetPath)

    if len(sys.argv) >= 2:
        question=sys.argv[1].decode(sys_type).encode("utf-8")
        result,new_question=parser.parse_question(question)
        result_str=""
        for key in result:
            result_str="{0}{1} : {2}\n".format(result_str,key,result[key])
        #winPrint("\n\nget: \n"+result_str)
    else:        
        #question_data="question_data.txt"
        question_data="new_questions.txt"
        data=getQuestionList(question_data)
        #print data["question"][0].decode("utf-8").encode("mbcs")    

        output=open("Data/parsed_data_new_dict.txt","w")
        
        keyword=[]
        for q in data["question"]:
            result,new_questions=parser.parse_question(q)
            keyword.append(result)
            # if len(result)>0:
            #     print type(result[0])
            #     winPrint(result[0])
            # for item in result:
            #     winPrint(item)
            # print "\n"    
            #output.write("{0}\n".format(result))
        
        for i in range(len(data["question"])):
            try:
                result_dict=keyword[i]
                result_str=""
                for key in result_dict:
                    result_str="{0}{1} : {2} ".format(result_str,key,",".join(result_dict[key]))
                output.write("{0},{1},{2},{3}\n".format(data["lable"][i],data["answer"][i],data["question"][i],result_str))

            except Exception as e:
                print str(e)
        output.close()    
