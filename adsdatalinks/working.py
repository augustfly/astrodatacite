
from collections import defaultdict
from simplejson import load

from BeautifulSoup import BeautifulStoneSoup

def countkeys(dictlist,
              dictkeys = ['bibcode','journal','pubyear']):
    t = {}
    keys = []
    for k in dictkeys:
        pkey = k+'s'
        keys.append(pkey)
        t[pkey] = defaultdict(int)

    for d in dictlist:
        for x,y in zip(keys,dictkeys):
            v = d.get(y)
            t[x][v] += 1
     
    return t

def repackdictlist(dictlist,
                   rkey = None):
    t = defaultdict(list)
    rkey = rkey and rkey or dictlist[0].keys()[0]

    for d in dictlist:
        v = d.get(rkey)
        t[v].append(d)
    
    return t
        
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

links = data['rows']
linkdict = repackdictlist(links,rkey='link type')
linktypes = linkdict.keys()

keys = ['bibcode','journal','pubyear']

dsl = linkdict['DatasetLink']

dsl_pubyear = repackdictlist(dsl,rkey="pubyear")

years = dsl_pubyear.keys()
years.sort()
for year in years:
    bibcodes = set()
    authors = set()
    yearlinks = dsl_pubyear[year]
    for link in yearlinks: 
        xbib = link['bibcode']
        xsrc = link['fulltext source file']
        if xbib not in bibcodes:
            surnames = surname(xsrc)
            authors.add(surnames[0])
            print year,xbib,surnames[0]
        bibcodes.add(xbib)
    print year, len(yearlinks), len(bibcodes), len(authors)

