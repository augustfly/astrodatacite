#!/usr/bin/env python

from ads_arXiv import parseADSXML, pparXiv, getSources, processSource, searchSource, loadadsJSON
from ads_arXiv import adsDIR, tags

import os, json

infile = 'query002.json'    

def _query(source, maxsearch=1, locale="ads", diskroot=adsDIR):
    """ root around arxiv source files for dataset ids
    """ 
    print 'query: % s' % source   
    try:
        data = loadadsJSON(source, validate=False, tags=tags)
    except:
        print 'json file did not parse fully'
        print 'will now treat as XML'
        data = parseADSXML(source, tags)
        #data = {}

    bibcodes = data.keys()
    for bib in bibcodes[:maxsearch]:
        print 'starting % s' % bib
        epid = pparXiv(data[bib]['eprintid'], auth='arXiv')
        datasets = []
        if epid != {}:
            wdir, sources = getSources(epid, 
                                       locale=locale, 
                                       diskroot=diskroot)
            content = []
            data[bib]['sources'] = []
            print sources
            for s in sources:
                f = os.path.join(wdir, s['file'])
                tcontent = processSource(f, type=s['type'],
                                         encoding=s['encoding'],
                                         action='read')
                if tcontent != []:
                    data[bib]['sources'].append(f)
                    content.extend(tcontent)
                                
            datasets = searchSource(content, cmd='dataset')
        else:
            print 'no eprint'
        data[bib]['datasets'] = datasets
        print '\n'
    return data

if __name__ == "__main__":
    data = _query(source=infile)
