
from collections import defaultdict
from simplejson import load

d = "../../../Data/astrodatacite/ADS/extlinks.json"
f = open(d,"r")
data = load(f)
f.close()

papers = data['rows']

linktypes = set()
for paper in papers:
    linktypes.add(paper['link type'])

linkdict = {}
for linktype in linktypes: 
    linkdict[linktype] = {'count':0,
                          'links':[],
                          'bibcodes':[],
                          'papers':[]}

for paper in papers:
    linkdict[paper['link type']]['count'] += 1
    linkdict[paper['link type']]['bibcodes'].append(paper['bibcode'])
    #linkdict[paper['link type']]['links'].append(paper['bibcode'])
    linkdict[paper['link type']]['papers'].append(paper)

keys = ['bibcode','journal','pubyear']
bibcodes = {'datasets':defaultdict(int)}
pubyears = {'bibcodes':defaultdict(int),'datasets':defaultdict(int)}
journals = {'bibcodes':defaultdict(int),'datasets':defaultdict(int)}

request = 'DatasetLink'
for w in linkdict[request]['papers']:
    b,j,y = (w.get(x) for x in keys)
    pubyears['datasets'][y] += 1
    journals['datasets'][j] += 1
    if b not in bibcodes['datasets'].keys():
        pubyears['bibcodes'][y] += 1
        journals['bibcodes'][j] += 1
    bibcodes['datasets'][b] += 1

