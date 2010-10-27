
from collections import defaultdict
from simplejson import load

d = "../../../Data/ADS/astrodatacite/extlinks.json"
f = open(d,"r")
data = load(f)
f.close()

papers = data['rows']

linktypes = set()
for paper in papers: linktypes.add(paper['link type'])

withdatasetlinks = [paper for paper in papers 
    if paper['link type'] == 'DatasetLink']

pubyears = defaultdict(int)
journals = defaultdict(int)
bibcodes = defaultdict(int)
keys = ['bibcode','journal','pubyear']
for w in withdatasetlinks:
    b,j,y = (w.get(x) for x in keys)
    pubyears[y] += 1
    journals[j] += 1
    bibcodes[b] += 1


