# coding: utf-8

import sys
import synonym
import re

f = open('resources/resultSimple.csv')
lines = [line.rstrip() for line in f.readlines()]

def anc(key):
    '''
    Return ancestors of the word `key` in ehownet.
    '''
    
    ans = []
    for i in range(len(lines)):
        if ' ' + key + '\t' in lines[i]:
            j = i
            while j > 0:
                pipe = lines[j].index('|')
                j -= 1
                
                while lines[j].index('|') >= pipe:
                    j -= 1
        
                line = lines[j]
                line = line[line.index('|')+2 : ]
                if '(' in line:
                    line = line[line.index('(')+1 : line.index(')')]
                    
                if '|' not in line:
                    ans.append(line)
                else:
                    ans.append([s for s in line.split('|') if not re.findall('\w', s)][0])
    
    while key in ans:
        ans.remove(key)
    return ans

def belong(a, b):
    '''
    Determine if `a` is a descendant of `b`.
    '''
    
    sa = set(anc(a))
    sb = set(synonym.synonym(b))
    
    return len(sb) > 0 and len(sa & sb) > 0

def get_type(word):
    if belong(word, '萬物'):
        return 'class'
    if belong(word, '行動'):
        return 'act'
    if belong(word, '屬性值'):
        return 'attr'
    return 'class'

def is_class(word):
    return belong(word, '萬物')

def is_act(word):
    return belong(word, '行動')

def is_attr(word):
    return belong(word, '屬性值')


if __name__ == '__main__':
    arg = sys.argv
    if len(arg) not in [2, 3]:
        print 'Usage:', arg[0], '<target>'
        sys.exit(-1)

    if len(arg) == 2:
        print '\n'.join(anc(arg[1]))
    else:
        print belong(arg[1], arg[2])
