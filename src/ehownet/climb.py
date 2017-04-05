import sys
import csv
import re
import ancestors
from os.path import abspath, dirname, join

content=[]

PATH = dirname(dirname(dirname(abspath(__file__))))
with open(join(PATH, 'resources/eHowNet_utf8.csv'), 'rb') as f:
    reader = csv.reader(f, delimiter='\t')
    for line in reader:
        content.append(line)
        
def climb(words, strict=True, shorter=False):
    '''
    Return a list of all definitions (expansions) of word in `words`.
    (`words` as a single word, instead of list, is acceptable)
    '''
    
    ans = []
    if isinstance(words, str):
        words = [words]
    global content
    for line in content:
        for word in words:
            if word in line and 'V' not in line[3]:
                for i in [5, 6]:
                    if line[i]:
                        if not strict or word not in line[i]:
                            if shorter:
                                if ':' in line[i]:
                                    ans.append(line[i])
                                    break
                                else:
                                    continue
                            else:
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
