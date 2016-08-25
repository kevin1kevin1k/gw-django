import sys
import csv
import re
import ancestors

def climb(words, strict=True):
    '''
    Return a list of all definitions (expansions) of word in `words`.
    (`words` as a single word, instead of list, is acceptable)
    '''
    
    ans = []
    if isinstance(words, str):
        words = [words]
    with open('resources/eHowNet_utf8.csv', 'rb') as f:
        lines = csv.reader(f, delimiter='\t')
        for line in lines:
            for word in words:
                if word in line:
                    for i in [5, 6]:
                        if line[i]:
                            if not strict or word not in line[i]:
                                ans.append(line[i])
    return ans

def climb_words(word):
    '''
    Return words that appear in the ehownet definition/expansion
    of `word`.
    '''
    
    ehs = climb(word, strict=False)
    ans = []
    for eh in ehs:
        words = re.split('[\w|{}=,:"~()]', eh)
        ans += filter(None, words)
    return list(set(ans))

if __name__ == '__main__':
    s = sys.argv[1]
    ancs = ancestors.anc(s) + [s]
    print '\n'.join(climb(ancs))
