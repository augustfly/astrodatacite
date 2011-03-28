
from listdict import *

from collections import defaultdict
from simplejson import load

from BeautifulSoup import BeautifulStoneSoup

def surname(filename):
    source = file(filename)
    parsed = BeautifulStoneSoup(source)
    source.close()
    names = [name.text for name in parsed.findAll('surname')]

    return names



d = "../../../Data/astrodatacite/ADS/extlinks.json"
f = open(d,"r")
data = load(f)
f.close()

linklist = data['rows']

keys = ['pubyear','journal','bibcode']


#linkdict = repacklistdict(linklist,dkey='link type')
#linktypes = linkdict.keys()
#
#
#dsl = linkdict['DatasetLink']
#
#dsl_pubyear = repacklistdict(dsl,dkey="pubyear")
#
#years = dsl_pubyear.keys()
#years.sort()
#authorstot = set()
#for year in years:
#    bibcodes = set()
#    authors = set()
#    yearlinks = dsl_pubyear[year]
#    for link in yearlinks: 
#        xbib = link['bibcode']
#        xsrc = link['fulltext source file']
#        if xbib not in bibcodes:
#            surnames = surname(xsrc)
#            authors.add(surnames[0])
#            #print year,xbib,surnames[0]
#        bibcodes.add(xbib)
#    print year, len(yearlinks), len(bibcodes), len(authors)
#    authorstot.update(authors)
#    print len(authorstot)

