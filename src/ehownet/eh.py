# coding: utf-8

from two import two
import ancestors
import parse_eh as pe
import climb
import re
import synonym

def common(l1, l2):
    '''
    Determine if two lists `l1` and `l2` have any common element.
    '''
    
    return set(l1) & set(l2) != set()

def get_conf(root, act_nodes, _ject, feats):
    '''
    Return a confidence according to the relationship
    between the object/subject (`_ject`) and `root`.
    `act_nodes` are telic/predication nodes, and
    `feats` are some common heads for objects/subjects.
    
    The returned confidence is currently determined
    by the following rules. However, a more general 
    approach should be adopted.
    '''
    
    # Rule 1: The children of `act_nodes` contains `_ject`.
    syns = synonym.synonym(_ject)
    for node in act_nodes:
        jects = [n.head for n in node.feat.values()]
        if common(jects, syns):
            return 0.9
    
    # Rule 2: `_ject` appears in the Tree rooted at `root`
    # on some node whose head belongs to `feats`.
    coll = root.collect()
    feat_heads = [head for f in feats for head in coll.get(f, [])]
    if common(feat_heads, syns):
        return 0.7
    
    # Rule 3: `_ject` appears in the Tree on any node.
    all_heads = [head for heads in coll.values() for head in heads]
    if common(all_heads, syns):
        return 0.6
    
    # None of the above
    return 0.1

def rules(a, b, is_class):
    '''
    Use some artificial rules to generate a list of
    (Y/U/N, confidence) pairs.
    '''
    
    ans = []
    if b in ['吃', '食用', '食物', '食品']:
        if a == '蛋':
            ans.append( ('Y', 1.0) )
        ans.append(two(a, '水果'))
        ans.append(two(a, '蔬菜'))
        ans.append(two(a, '莊稼'))
        if b != '食物':
            ans.append(two(a, '食物'))
        if b != '食品':
            ans.append(two(a, '食品'))
    if b in ['喝', '飲用']:
        ans.append(two(a, '湯'))
        ans.append(two(a, '飲品'))
        ans.append(two(a, '飲料'))
    if b in ['看', '讀', '閱讀', '紙']:
        ans.append(two(a, '讀物'))
    if b in ['呼吸', '活', '活的', '生命']:
        ans.append(two(a, '生物'))
    if b == '飛':
        ans.append(two(a, '禽'))
    if b in ['液', '液狀', '液體']:
        ans.append(two(a, '液態', is_class))
    if b in ['硬', '堅硬', '延展性', '光澤']:
        ans.append(two(a, '金屬'))
    if b in ['電', '電力', '儀器']:
        ans.append(two(a, '機器'))
    if b in ['聲音', '音樂']:
        ans.append(two(a, '樂器'))
    if b in ['家裡', '家中']:
        ans.append(two(a, '家具'))
        ans.append(two(a, '炊具'))
        ans.append(two(a, '餐具'))
        ans.append(two(a, '寢具'))
    if b in ['日常', '常見']:
        ans.append(two(a, '家具'))
        ans.append(two(a, '用具'))
    if b in ['飛', '飛行', '飛翔', '翱翔', '空中', '天空', '天上']:
        ans.append(two(a, '飛行器'))
    if b in ['搭', '乘', '搭乘', '乘坐']:
        ans.append(two(a, '交通工具'))    
    if b in ['地方', '建築', '場所', '建築物']:
        ans.append(two(a, '機構'))
        if b != '建築物':
            ans.append(two(a, '建築物'))
        if b != '場所':
            ans.append(two(a, '場所'))
    if b in ['工具', '用具', '用品']:
        ans.append(two(a, '器具'))
    
    ans = [i for i in ans if i[0] == 'Y']
    if b in ['生物', '動物'] and ancestors.belong(a, '身體部件'):
        ans.append( ('N', 1.0) )
    return [two(a, b, is_class)] + ans

def decide(lst):
    '''
    Decide the answer based on the list `lst`
    of (Y/U/N, confidence) pairs.
    
    Current algorithm: 
    (1) No Y and no N: return U with conf 1.0
    (2) Otherwise: the answer with higher maximum
        confidence wins.
    '''
    
    ymax, nmax = 0, 0
    for i in range(len(lst)):
        if   lst[i][0] == 'Y' and lst[i][1] > ymax:
            ymax = lst[i][1]
        elif lst[i][0] == 'N' and lst[i][1] > nmax:
            nmax = lst[i][1]
    if ymax == nmax == 0:
        return 'U', 1.0
    if ymax >= nmax:
        return 'Y', ymax
    return 'N', nmax

def run(a, d):
    '''
    With answer `a` and keyword dict `d` as input,
    returns a (Y/U/N, confidence) pair.
    '''
    
    is_class = 'class' in d
    ans = []
    
    if 'attr' in d:
        ans.append(two(a, d['attr'], 'a'))
    
    if 'class' in d:
        ans.append(two(a, d['class'], 'c'))
    
    if 'location' in d:
        ehs = climb.climb(a)
        for eh in ehs:
            eh = re.sub('(\|\w+)|(\w+\|)', '', eh)
            root = pe.parse(eh)
            coll = root.collect()
            syns = synonym.synonym(d['location'])
            if common(coll.get('location', []), syns):
                ans.append( ('Y', 1.0) )
    
    if 'act' in d:
        # object examples: 公鹿 水雷 牙科醫生 
        has_obj = 'object' in d
        has_sub = 'subject' in d
        ehs = climb.climb(ancestors.anc(a) + [a])
        for eh in ehs:
            eh = re.sub('(\|\w+)|(\w+\|)', '', eh)
            root = pe.parse(eh)
            act_nodes = []
            for k, v in root.feat.items():
                for act in ['telic', 'predication']:
                    if act in k: # cases of 'telic+', etc.
                        act_nodes.append(v)
            syns = synonym.synonym(d['act'])
            if common([n.head for n in act_nodes], syns):
                if has_obj:
                    feats = ['patient', 'theme', 'content', 'target']
                    conf = get_conf(root, act_nodes, d['object'], feats)
                elif has_sub:
                    feats = ['agent', 'domain', 'instrument']
                    conf = get_conf(root, act_nodes, d['subject'], feats)
                else:
                    conf = 0.9
                    
                if conf >= 0.5:
                    ans.append( ('Y', conf) )                  

    tmp = [decide(rules(a, b, is_class)) for b in d.values()]
    tmp_nu = [i[1] for i in tmp if i[0] != 'Y']
    if tmp_nu:
        tmp_n = [i[1] for i in tmp if i[0] == 'N']
        if tmp_n:
            avg = sum(tmp_n) / len(tmp_n)
            ans.append( ('N', avg) )
    else:
        avg = sum([i[1] for i in tmp]) / len(tmp)
        ans.append( ('Y', avg) )
    
    return decide(ans)


if __name__ == '__main__':
    print run('蜜蜂', {'act': '採集', 'object': '食品'}) # 0.9
    print run('蜜蜂', {'act': '採集', 'object': '花草'}) # 0.6
    print run('責任準備金', {'act': '保證', 'object': '錢'}) # 0.7
    
    # If the answer itself is the subject, 
    # and the parser gives no subject, 
    # maybe a '~' can be passed to run().
    print run('送貨員', {'act': '運送', 'subject': '~'})
    print run('牙醫', {'act': '醫治', 'subject': '~'})
    
    print run('客廳', {'class': '場所'})
    