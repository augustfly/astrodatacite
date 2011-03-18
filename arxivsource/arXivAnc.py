#!/usr/bin/env python

from ads2arXiv import *
from pprint import pprint as ppp

import mimetypes as mime

import os, json

maxsearch = 100000
locale = 'ads'
jsnfile = 'aas2009.json'
xmlfile = 'aas2009_references.xml'
adsDIR = '/proj/adsduo/abstracts/sources/ArXiv/fulltext'
fkeys = ['bibcode','eprintid','file','extension','mimetype','encoding','pathlength']

_key_formater = {}
_key_formater['file'] = lambda x:x
_key_formater['extension'] = lambda x:os.path.splitext(x)[1][1:]
_key_formater['mimetype'] = lambda x:mime.guess_type(x)[0] or 'extension/'+os.path.splitext(x)[1][1:]
_key_formater['encoding'] = lambda x:mime.guess_type(x)[1] 
_key_formater['pathlength'] = lambda x:len(x.split(os.path.sep))-1


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
                    finfo = []
                    finfo.extend(binfo)
                    for k in fkeys[2:]:
                        finfo.append(_key_formater[k](t))

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
