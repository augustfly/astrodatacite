#!/usr/bin/env python

from ads2arXiv import *
from pprint import pprint as ppp

import mimetypes as mime

import os, json

maxsearch = 10
locale = 'ads'
jsnfile = 'aas2009.json'
xmlfile = 'aas2009_references.xml'
adsDIR = '/proj/adsduo/abstracts/sources/ArXiv/fulltext'
fkeys = ['bibcode','eprintid','file','extension','mimetype','encoding','pathlength']


def tabulate_files(query=xmlfile, maxsearch=1, locale='ads',
         diskroot=adsDIR, urlroot=arxivURL):
    """ main
    """ 
    print 'query: % s' % query   
    data = parseADSXML(query, tags)

    bibcodes = data.keys()
    files = []
    for bib in bibcodes[:maxsearch]:
        print '\nstarting % s' % bib
        print 'eprintid %s' % data[bib]['eprintid']
        epid = pparXiv(data[bib]['eprintid'], auth='arXiv')
        datasets = []
        binfo = [bib,data[bib]['eprintid']]
        if epid != {}:
            wdir, sources = getSources(epid, locale,
                                       diskroot=diskroot, urlroot=urlroot)
            content = []
            data[bib]['sources'] = []
            print sources
            for s in sources:
                f = os.path.join(wdir, s['file'])
                tcontent = processSource(f, type=s['type'],
                                         encoding=s['encoding'],
                                         action='tlist')
                #[bib,t,ext,mime,pathlenght]
                print tcontent
                for t in tcontent:
                    finfo = binfo
                    finfo.append(t)
                    finfo.append(os.path.splitext(t)[1])
                    finfo.extend(mime.guess_type(t))
                    finfo.append(len(t.split(os.path.sep))-1)
                    files.append(dict(zip(fkeys,finfo)))
                    print finfo
        else:
            finfo = binfo
            finfo.extend([None,None,None,None,None])
            files.append(dict(zip(fkeys,finfo)))
    return files 



if __name__ == "__main__":
    data = tabulate_files(query=xmlfile, 
                          maxsearch=maxsearch, 
                          locale=locale,
                          diskroot=adsDIR)
    json.dump(data,file(jsnfile,'w+'),ensure_ascii=False,indent=2)
