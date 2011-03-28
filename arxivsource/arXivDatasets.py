#!/usr/bin/env python

from ads_arXiv import parseADSXML, pparXiv, getSources, processSource, searchSource, loadadsJSON
from ads_arXiv import adsDIR, default_tags

import os, json, sys

infile = 'query002.json'    

def _query(source, maxsearch=1, locale="ads", diskroot=adsDIR):
    """ root around arxiv source files for dataset ids
    """ 
    print 'query: % s' % source   
    try:
        data = loadadsJSON(source, validate=False, tags=default_tags)
    except:
        print 'json file did not parse fully'
        print 'will now treat as XML'
        data = parseADSXML(source, default_tags)
        #data = {}

    bibcodes = data.keys()
    print 'total bibcodes: %s' % len(bibcodes)
    sets = []
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
        if datasets != []:
            sets.append(data[bib])
        print '\n'
    return sets, data

defs = {}
defs['source'] = lambda x:os.path.exists(x) and x or None
defs['outfile'] = lambda x:x != "" and x or "default" 
defs['maxsearch'] = lambda x:x != "" and long(x) or 1L
defs['indent'] = lambda x:x != "" and int(x) or None

def main(argv=None):
    args = defs.keys()
    larg = len(args)

    if argv == None:
        if sys.argv[1:] == []:
            print 'cmd variables are in order: ',args
            return
        argv = []
        argv.extend(sys.argv[1:])
        argv.extend([""]*larg)
        argv = argv[:larg]

    for i,arg in enumerate(args):
        argv[i] = defs[arg](argv[i])

    argd = dict(zip(args,argv))

    if argd['source'] is None:
        raise Exception("no valid input file")

    sets, data = _query(source=argd['source'], maxsearch=argd['maxsearch'])
    with file(argd['outfile'],'w+') as f:
        json.dump(sets, f, ensure_ascii=False, indent=argd['indent'])

if __name__ == "__main__":
    sys.exit(main())

