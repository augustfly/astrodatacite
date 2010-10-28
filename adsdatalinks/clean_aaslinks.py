
import csv
# from pp import ppBibCode
import urlparse
import random

clean = {}
clean['bibcode'] = lambda x: x
#clean['bibcode'] = lambda x: ppBibCode(x)
#clean['link'] = lambda x: x.split(' ')[0]
clean['link'] = lambda x: urlparse.urlparse(x.split(' ')[0])
clean['label'] = lambda x: x.split(' ')[1:]
clean['label'] = lambda x: x.split(' ')[1:]

process_row = lambda x: x[0].split('\t')

def cleanrow(l):
    d = {}
    d['bibcode'] = clean['bibcode'](l[0])
    d['link'] = clean['link'](l[1])
    d['label'] = clean['label'](l[1]) or ''
    return d

def cleantable(t):
    pass

d="../../../Data/astrodatacite/ADS/all.links"
f = open(d,'r')
reader = csv.reader(f)
data = []
for row in reader: data.append(process_row(row))
f.close()

datadict = []
for row in data: datadict.append(cleanrow(row))

for x in range(0,10): print random.choice(datadict)
