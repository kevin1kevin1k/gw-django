#! python2
# coding: utf-8
import re

class TreeNode:
    def __init__(self, _data = ''):
        self.child = []
        self.data = _data

def put(s, node):
    first_par = s.find('(')
    if first_par == -1:
        node.data = s
        return
    
    node.data = s[ : first_par]
    
    # if s.find(')') == -1:
    #     rest = s[first_par+1 : ]
    # else:
    rest = s[first_par+1 : -1]
    # print rest
    
    balanced = []
    cnt = 0
    n = len(rest)
    for i in range(n):
        if rest[i] == '(':
            cnt += 1
        elif rest[i] == ')':
            cnt -= 1
        balanced.append(cnt == 0)
    # print balanced
    
    pipe_idx = [i for i in range(n) if rest[i] == '|' and balanced[i]]
    pipe_idx.insert(0, -1);
    pipe_idx.append(n);
    # print pipe_idx
    
    for i in range(len(pipe_idx) - 1):
        part = rest[pipe_idx[i]+1 : pipe_idx[i+1]]
        # print 'part:', part
        
        baby = TreeNode()
        put(part, baby)
        node.child.append(baby)
    
def show(node, depth = 0):
    print '\t' * depth + node.data
    if len(node.child) != 0:
        for i in node.child:
            show(i, depth + 1)

def getAllLeafNodes(node):
    answer = []
    if not node.child:
        answer.append(node.data.split(':')[-1])
    for c in node.child:
        answer += getAllLeafNodes(c)
    return answer

def getTargetNode(node,s,method="dfs"):
    if method.lower() =="dfs":
        if re.search(s,node.data) is not None: #包含指定的字串
            return node
        if len(node.child)==0:
            return None 
        for child in node.child:
            result= getTargetNode(child,s)
            if result is not None:
                return result
        return result
    elif method.lower()=="bfs":
        return getTargetNodeBFS(node,s,True) 
    #else:      

def getTargetNodeBFS(node,s,isRoot=False):

    if isRoot:
        if re.search(s,node.data) is not None: #包含指定的字串
            return node

    if len(node.child)==0:
        return None 
        
    for child in node.child:
        if re.search(s,child.data) is not None: #包含指定的字串
            return child
    for child in node.child:        
        result= getTargetNodeBFS(child,s)
        if result is not None:
            return result
    return result

def getTargetLeafNode(node,s):
    if len(node.child)==0 and re.search(s,node.data) is not None:
        return node 
    if len(node.child)!=0:    
        for child in node.child:
            result= getTargetLeafNode(child,s)
            if result is not None:
                return result
    else:
        return None

"""回傳list of node"""        
def getAllTargetLeafNode(node,s,result_lst):
    if len(node.child)==0 and re.search(s,node.data) is not None:
        result_lst.append(node)
        return result_lst

    if len(node.child)!=0:
        for child in node.child:
            result_lst=getAllTargetLeafNode(child,s,result_lst)
    return result_lst

"""找其小孩有包含指定字串的node 規則要傳unicode!!"""
def getTargetParentNode(node,s):
    if len(node.child)==0:
        return None
    child_data=[child.data for child in node.child]
    child_data_str=" ".join(child_data).decode("utf-8")
    if re.search(s,child_data_str) is not None: #包含指定的字串
        return node
        
    for child in node.child:
        result= getTargetParentNode(child,s)
        if result is not None:
            return result
    return result

"""找包含指定字串,且其小孩不包含排除字串的node"""
def getTargetNodeExcept(node,s,except_str):   
    if re.search(s,node.data) is not None :#包含指定的字串
        match=False
        for ch in node.child:
            if re.search(except_str,ch.data) is not None: 
                match=True
        if not match:        
            return node
    if len(node.child)==0:
        return None 
    for child in node.child:
        result= getTargetNodeExcept(child,s,except_str)
        if result is not None:
            return result
    return result

def create_tree(s):
    root=TreeNode()
    put(s,root)
    return root            