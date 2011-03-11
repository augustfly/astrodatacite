
from collections import defaultdict
from simplejson import load

from BeautifulSoup import BeautifulStoneSoup

def countkeys(listdict,
              dictkeys = ['bibcode','journal','pubyear']):
    t = {}
    keys = []
    for k in dictkeys:
        pkey = k+'s'
        keys.append(pkey)
        t[pkey] = defaultdict(int)

    for d in listdict:
        for x,y in zip(keys,dictkeys):
            v = d.get(y)
            t[x][v] += 1
     
    return t

def repacklistdict(ll, dkey = None):
    """ repack a list of dictionaries as a dictionary of lists 
        keyed on one of the dictionary keys.
    """
    t = defaultdict(list)
    dkey = dkey and dkey or ll[0].keys()[0]

    for d in ll:
        v = d.get(dkey)
        t[v].append(d)
    
    return t
        
def ld_keycount(ld, keys=[None,None,None]):
    kl = []
    for key in keys: 
        dl = repacklistdict(ld,dkey=key)
        dk = dl.keys()
        dk.sort()
        kl.append(dk)

    dl = repacklistdict(ld,dkey=keys[0])

    h = "%7s " % (keys[0])
    for i in kl[1]:
        h = h + "%7s " % (i)
    print h

    zt = 0
    for y in kl[0]:
        h = "%7s " % (y)
        ly = dl[y]
        dx = repacklistdict(ly,dkey=keys[1])
        z = []
        for x in kl[1]:
            lz = dx.get(x)
            dz = lz and repacklistdict(lz,dkey=keys[2]) or []
            z.append(len(dz))
            h = h + "%7s " % (len(dz))
        zt += sum(z)
        print h

    return zt
    
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

