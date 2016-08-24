import sys
import csv
import re
import climb
import ancestors
import synonym

def one(w):
    '''
    Return a list of lines where `w` appears.
    '''
    
    ans = []
    with open('eHowNet_utf8.csv', 'rb') as f:
        lines = csv.reader(f, delimiter='\t')
        for l in lines:
            if any([w in s for s in l]):
                ans.append(' '.join([l[1], l[5], l[6]]))
    return ans

def prob(a, b):
    '''
    Given two words `a` and `b`, 
    return the estimated conditional occurrence frequency (?),
    or more precisely, P(`b` | `a`).
    '''
    
    oa = one(a)
    ob = [s for s in oa if re.search('[{}|:]'+b+'[{}|:]', s)]
    denom = len(oa)
    num = len(ob)
    return 0 if denom == 0 else 1.0 * num / denom

def scale(x):
    '''
    Scale up `x` in [0, 1] so that the predicted confidence
    is not too low.
    
    If 0.4 is set to be smaller, then small values of `x`
    will be better-scaled, but large values of `x`
    will become too close to 1.
    '''
    
    return x ** 0.4

def two(a, b, is_class=True):
    '''
    Given answer `a` and keyword `b`, do the following:
    
    (1) If `a` belongs to `b`, return Y.
    (2) Otherwise, and if it's a class-type question,
        then return N.
    (3) Otherwise, if the definitions of `a` contains `b`, 
        then return Y.
    (4) Otherwise, if `a` and `b` co-occur, 
        return their co-occurrence frequency (scaled).
    (5) Otherwise, return U.
    '''
    
    # (1)
    if ancestors.belong(a, b):
        conf = 1 if is_class else 0.8
        return 'Y', conf
    
    # (2)
    if is_class:
        return 'N', 1.0
    
    # (3)
    syn = ['[{|:]'+s+'[}|:]' for s in synonym.synonym(b) if s != '']
    cmb = climb.climb(ancestors.anc(a) + [a])
    cnt = 0
    for c in cmb:
        for s in syn:
            if re.search(s, c):
                cnt += 1
                break
    if cnt > 0:
        return 'Y', scale(1.0 * cnt / len(cmb))
    
    # (4)
    pab, pba = prob(a, b), prob(b, a)
    if pab > 0 and pba > 0:
        return 'Y', scale((pab + pba) / 2)
    
    # (5)
    return 'U', 1.0
    
if __name__ == '__main__':
    arg = sys.argv
    is_class = (arg[3] == 'c') if len(arg) == 4 else True
    print two(arg[1], arg[2], is_class)
