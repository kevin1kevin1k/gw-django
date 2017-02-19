#! python2
# -*- coding: UTF-8 -*-
import urllib
from urllib2 import Request, urlopen

def translate(q,sl,tl):
    '''
        q: input string,
        sl: source language,
        tl: target language,
    '''
    query = urllib.urlencode({'q' : q,'dt':'t', 'sl':sl, 'tl':tl,'client':'gtx'})
    url = "https://translate.googleapis.com/translate_a/single?{}".format(query)

    req = Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0')
    req.add_header('Accept', 'application/json')
    resp = urlopen(req)
    content = resp.read()
    result = content.split(',')[0].replace('[','').replace('"','')
    return result