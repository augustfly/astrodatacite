"""
    functions for dealing with "list dicts" 
    listdicts are lists of dictionaries containing mostly well classed lists
    these examples were written for dealing with ads xml files
"""

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
        
def countkeys(listdict,
              dictkeys = ['bibcode','journal','pubyear']):
    """ count keys in listdict
    """
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

def ld_keycount(ld, keys=[None,None,None]):
    """ 
    """
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
