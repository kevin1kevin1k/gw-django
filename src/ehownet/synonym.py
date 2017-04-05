# coding: utf-8

import sys
from os.path import abspath, dirname, join

PATH = dirname(dirname(dirname(abspath(__file__))))
f = open(join(PATH, 'resources/resultSimple.csv'))
lines = [line.rstrip() for line in f.readlines()]

def check(word, line):
    '''
    Check if `line` needs processing with respect to `word`.
    '''
    
    if ' ' + word + '\t' in line:
        return True
    s = '|' + word
    if line[-len(s):] == s:
        return True
    
    return False

def synonym(key):
    '''
    Find all the synonyms of `key` (including itself)
    and return them as a list.
    '''
    
    ans = {key}
    for i in range(len(lines)):
        line = lines[i]
        if check(key, line):
            if line[0] == ' ':
                continue
            pipe = line.index('|')
            j = i
            if line[0] != ',':
                while lines[j].index('|') >= pipe:
                    j -= 1
            
            pipe = lines[j].index('|')
            ans.add(lines[j].split('|')[-1])
            j += 1
            while j < len(lines):
                line = lines[j]
                c = line[0]
                if c in '.,' and line.index('|') == pipe:
                    break
                if c == '+' and line.index('|') == pipe + 1:
                    ans.add(line.split(' ')[1].split('\t')[0])
                j += 1
                    
    return list(ans)

if __name__ == '__main__':
    arg = sys.argv

    if len(arg) == 2:
        target = arg[1]
        print '\n'.join(synonym(target))
