import sys
import csv
import ancestors

def climb(words):
    '''
    Return a list of all definitions (expansions) of word in `words`.
    (`words` as a single word, instead of list, is acceptable)
    '''
    
    ans = []
    if isinstance(words, str):
        words = [words]
    with open('eHowNet_utf8.csv', 'rb') as f:
        lines = csv.reader(f, delimiter='\t')
        for l in lines:
            for w in words:
                if w in l:
                    for i in [5, 6]:
                        if l[i] != '' and w not in l[i]:
                            ans.append(l[i])
    return ans

if __name__ == '__main__':
    s = sys.argv[1]
    ancs = ancestors.anc(s) + [s]
    print '\n'.join(climb(ancs))
