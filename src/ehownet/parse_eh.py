# coding: utf-8

import re
from node2str import node2str
import climb
class Tree:
    '''
    A tree structure for the representation of the parsed result
    of an ehownet definition/expansion whose head is `head` (?).
    `feat` is its features (children),
    and `parent` tells about itself.
    '''

    def __init__(self, _head = ''):
        self.head = _head
        self.feat = {}
        self.parent = None
    
    def get_depth(self):
        if self.head == '~':
            return -1
        if not self.feat:
            return 0
        return 1 + max([self.feat[i].get_depth() for i in self.feat])
    
    def traverse(self, depth=0):
        '''
        Print out the Tree structure rooted at `self`.
        '''
        
        print self.head
        if self.feat:
            for k in self.feat:
                print '  ' * (depth+1) + k,
                self.feat[k].traverse(depth + 1)
    
    def collect(self):
        '''
        Return a dict which maps a feature to a list of corresponding heads.
        '''
        
        f = self.feat
        if f == {}:
            return {}
        
        ans = {}
        for k, n in f.items():
            k = k.rstrip('+')
            if k not in ans:
                ans[k] = []
            if n.head == '~':
                nn = n.parent.parent
            else:
                nn = n
            ans[k].append(nn.head)
            
            for k1, heads in n.collect().items():
                k1 = k1.rstrip('+')
                if k1 not in ans:
                    ans[k1] = []
                ans[k1] += heads
        
        return ans
    
    def find(self, word):
        '''
        Find out the Tree with `word` as its head
        in the Tree rooted at `self`,
        and return the Tree or None if `word` was not found
        '''
        
        if self.head == word:
            return self
        
        f = self.feat
        for k in f:
            n = f[k].find(word)
            if n:
                return n

        return None

def parse(s):   
    '''
    Return a Tree constructed from `s`
    '''
    
    if s[-2] == ')':
        par = s.find('(')
        node = Tree(s[1 : par])
        rest = s[par+1 : -2]
        # assume there is no nested ',' in rest
        parts = rest.split(',')
        for part in parts:
            node.feat[part] = parse(part)
            node.feat[part].parent = node
        return node
        
    colon = s.find(':')
    node = Tree(s[1 : colon])
    if colon == -1:
        return node
    
    rest = s[colon+1 : -1]
    balanced = []
    cnt = 0
    n = len(rest)
    for i in range(n):
        if rest[i] == '{':
            cnt += 1
        elif rest[i] == '}':
            cnt -= 1
        balanced.append(cnt == 0)
    
    idx = [i for i in range(n) if rest[i] == ',' and balanced[i]]
    idx.insert(0, -1);
    idx.append(n);
    
    for i in range(len(idx) - 1):
        part = rest[idx[i]+1 : idx[i+1]]
        equal = part.find('=')
        left, right = part[ : equal], part[equal+1 : ]
        while left in node.feat:
            left += '+'
        node.feat[left] = parse(right)
        node.feat[left].parent = node
        
    return node

def def2sentence(node, max_depth=-1):
    '''
    Input: A Tree node and an optional max_depth
    Output: The sentence constructed from the definition implied by node 
    '''
    
    depth = node.get_depth()
    if 0 <= max_depth < depth:
        depth = max_depth
    
    head = node.head
    if depth == 0:
        return head
    links = {}
    for f, n in node.feat.items():
        if '~' not in n.head:
            links[f] = def2sentence(n, depth - 1)
    
    ans = node2str(head, links)
    return ans

if __name__ == '__main__':
    # sample ehownet definitions/expansions
    l = [
        '{edge({飛機|airplane}):telic={fly|飛:instrument={~}},predication={alike|似:theme={~},contrast={wing|翅}},quantity={1}}',
        '{InsectWorm|蟲:predication={gather|採集:theme={food|食品:source={FlowerGrass|花草}},agent={~}}}',
        '{beast|走獸:predication={swim|游:theme={~},location={海|sea}}}',
        '{家電|HouseholdElectricalAppliances:telic={store|保存:theme={edible|食物},location={~},means={cool|製冷}}}',
        '{clothing|衣物:telic={block|攔住:theme={RainSnow|雨雪},instrument={~}}}',
        '{BeAcross|相交:theme={edge({country|國家})}}',
        '{人:domain={醫},predication={醫治:patient={PartOf({口}):predication={啃咬:instrument={~}}},agent={~}}}',
        '{human|人:predication={transport|運送:agent={~},theme={artifact|人工物:predication={and({buy|買:possession={~}},{sell|賣:possession={~}})}}},predication={employ|僱用:patient={~}}}',
        '{expenditure|費用:telic={guarantee|保證:content={pay|付:theme={money|貨幣},while={suffer|遭受:content={mishap|劫難}},agent={InstitutePlace|場所:domain={economy|經濟},telic={sell|賣:theme={affairs|事務:CoEvent={guarantee|保證},domain={economy|經濟}},agent={~}}}},price={~}}}',
        '{human|人:predication={keep|保持:agent={~},theme={safety({place|地方}):domain={police|警}}},telic={defend|防守:theme={InstitutePlace|場所:domain={education|教育},telic={and({study|學習:location={~}},{teach|教:location={~}})}},agent={~}}}'
    ]
    
    # from climb import climb
    # while 1:
    #     answer = raw_input().split()
    #     depth = 1 if len(answer) == 1 else int(answer[1])
    #     answer = answer[0]
    # 
    #     defs = climb(answer, strict=False, shorter=True)
    #     if defs:
    #         definition = defs[0]
    #         definition = re.sub('(\|\w+)|(\w+\|)', '', definition)
    #         print definition
    #         def_root = parse(definition)
    #         # depth = def_root.get_depth()
    #         # print 'depth', depth
    #         print def2sentence(def_root, depth)
    #         print
    
    # for s in l:
    #     # remove unnecessary English
    #     s = re.sub('(\|\w+)|(\w+\|)', '', s)
    #     print s
    #     root = parse(s)
    #     # root.traverse()
    #     print def2sentence(root)
    #     print
        
    #     # for k, v in root.collect().items():
    #     #     print k, ','.join(v)
    #     # print

    test=['進口商', '蜜蜂', '雨靴', '冰箱', '理賠','鍋子','螃蟹','電話','牙醫師','鑰匙','三明治','單翼','蛇','代書',
            '鯨魚','布丁','河','茶','火藥','銀行','牛','火車','手電筒','閃電','披薩','櫃子','太空衣','未婚夫','口罩','心肌']
    for term in test:
        defs = climb.climb(term, strict=False, shorter=True)
        if defs:
            definition = defs[0]
            definition = re.sub('(\|\w+)|(\w+\|)', '', definition)
            print(definition)
            def_root = parse(definition)
            max_depth = def_root.get_depth()
            print(def2sentence(def_root, max_depth))
        else:
            print('no def')