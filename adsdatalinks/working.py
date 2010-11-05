
from collections import defaultdict
from simplejson import load

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
        

d = "../../../Data/astrodatacite/ADS/extlinks.json"
f = open(d,"r")
data = load(f)
f.close()

links = data['rows']
linkdict = repackdictlist(links,rkey='link type')
linktypes = linkdict.keys()

keys = ['bibcode','journal','pubyear']

