# coding: utf-8

import re
from node2str import node2str

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

def def2sentence(node, max_depth=2):
    head = node.head
    if max_depth == 0:
        return head
    links = {}
    for f, n in node.feat.items():
        if n.head != '~':
            links[f] = def2sentence(n, max_depth - 1)
    return node2str(head, links)

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
    
    for s in l:
        # remove unnecessary English
        s = re.sub('(\|\w+)|(\w+\|)', '', s)
        print s
        root = parse(s)
        root.traverse()
        for k, v in root.collect().items():
            print k, ','.join(v)
        print
