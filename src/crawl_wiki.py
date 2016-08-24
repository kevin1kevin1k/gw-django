# encoding: utf-8

from bs4 import BeautifulSoup
import urllib
from TranslationTool.langconv import Converter
import cPickle as pickle
from crawlData import getSimilarity as sim
from question_parser import segmentSentence as segment
import sys

class Tree:
    '''
    A tree structure storing information of all wiki pages 
    down from the page with category `title`.
    `Depth` describes itself.
    `Items` are the titles of leaf pages, 
    and `kids` are the sub-Trees (subcategories in wiki).
    
    '''
    
    def __init__(self, _title='', _depth=0):
        self.title = _title
        self.depth = _depth
        self.items = []
        self.kids = []
    
    def traverse(self):
        # '-' means category, '.' means items(?)
        
        for i in self.items:
            print '.' * self.depth + i
        for k in self.kids:
            print '-' * self.depth + k.title
            k.traverse()


def crawl_up(s, depth=1, verbose=True, history=None, answer=None):
    '''
    Crawl wiki upwards from the page with word `s`.
    The structure is printed out if `verbose` is True.
    It stops when similarity(original word, current word) < 0.3 .
    '''
    
    if not history:
        history = {}
    if not answer:
        answer = s
    if depth > 1:
        s = 'Category:' + s
    
    url = 'https://zh.wikipedia.org/zh-tw/' + s
    try:
        html = urllib.urlopen(url)
    except:
        with open('error.log', 'a') as err:
            err.write(url + '\n')
        return history
    soup = BeautifulSoup(html, 'lxml', from_encoding='utf-8')
    html.close()
    converter = Converter('zh-hant')
    
    cats = soup.find_all('div', attrs={'class': 'mw-normal-catlinks'})
    for div in cats:
        for li in div.find_all('li'):
            title = converter.convert(li.a.text).encode('utf-8')
            if title not in history:
                # higher threshold => higher precision and lower recall
                # and we care more about precision
                try:
                    segs = segment(title)
                    if all([sim(answer, w) < 0.3 for w in segs]):
                        continue
                except:
                    with open('error.log', 'a') as err:
                        err.write(answer + '\t' + title + '\n')
                    continue
                if verbose:
                    print '-' * depth + title
                history[title] = depth
                kid = crawl_up(title, depth + 1, verbose, history, answer)        

    return history

def crawl_file_to_pkl(filename='answer200.txt', verbose=True):
    '''
    Read the file `filename` line by line,
    (each line should contains a single word)
    for each line call `crawl_up` and save the history result.
    Put all the (line, history) pair into a dict,
    and pickle up to a .pkl file for future usage.
    '''
    
    d = {}
    with open(filename, 'r') as infile:
        for line in infile:
            word = line.rstrip()
            if verbose:
                print word
            d[word] = crawl_up(word, verbose=False)
        
        dot = filename.find('.')
        if dot == -1:
            prefix = filename
        else:
            prefix = filename[ : dot]
        with open(prefix + '.pkl', 'wb') as outfile:
            pickle.dump(d, outfile, pickle.HIGHEST_PROTOCOL)

def load_pkl_to_dict(filename='answer200.pkl'):
    '''
    Return a dict which maps keyword to a dict
    which maps upstream words to their depths.
    '''
    
    with open(filename, 'rb') as infile:
        return pickle.load(infile)

def crawl_down(s, depth=1, make_tree=False, verbose=True):
    '''
    Crawl wiki downwards from the category `s`.
    The structure is printed out if `verbose` is True.
    If `make_tree` is True, it returns the root;
    otherwise it returns None.
    '''
    
    if make_tree:
        node = Tree(s, depth)
    
    html = urllib.urlopen('https://zh.wikipedia.org/zh-tw/Category:' + s)
    soup = BeautifulSoup(html, 'lxml', from_encoding='utf-8')
    converter = Converter('zh-hant')
    
    pages = soup.find_all('div', attrs={'id': 'mw-pages'})
    for div in pages:
        for li in div.find_all('li'):
            title = converter.convert(li.a['title']).encode('utf-8')
            if verbose:
                print '.' * depth + title
            if make_tree:
                node.items.append(title)
    
    cats = soup.find_all('div', attrs={'id': 'mw-subcategories'})
    for div in cats:
        for li in div.find_all('li'):
            title = converter.convert(li.a.text).encode('utf-8')
            if verbose:
                print '-' * depth + title
            
            kid = crawl_down(title, depth + 1, make_tree, verbose)    
            if make_tree:
                node.kids.append(kid)

    return node

if __name__ == '__main__':
    # d = crawl_up('熊貓', verbose=True)
    # for word in d:
    #     print word, d[word]
    
    arg = sys.argv
    if len(arg) > 1:
        crawl_file_to_pkl(arg[1])
    else:
        crawl_file_to_pkl()
    # wiki = load_pkl_to_dict()
    # for word in wiki:
    #     print word
    #     print ','.join(wiki[word].keys())
    #     print
    
    # root = crawl_down('海豹科', make_tree=True, verbose=True)
    # root.traverse()
