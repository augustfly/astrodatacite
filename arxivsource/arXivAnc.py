#!/usr/bin/env python

from ads_arXiv import parseADSXML, tagFormat, getSources, processSource, pparXiv, loadadsJSON
from ads_arXiv import adsDIR, default_tags
from pprint import pprint as ppp
import mimetypes as mime
import os, json, sys

fkey_formats = {}
fkey_formats['file'] = lambda x:x
fkey_formats['extension'] = lambda x:os.path.splitext(x)[1][1:]
fkey_formats['mimetype'] = lambda x:mime.guess_type(x)[0] or \
                           'extension/'+os.path.splitext(x)[1][1:]
fkey_formats['encoding'] = lambda x:mime.guess_type(x)[1] 
fkey_formats['pathlength'] = lambda x:len(x.split(os.path.sep))-1
fkeys = ['file','extension','mimetype','encoding','pathlength']
n_fkeys = len(fkeys)

def _tabulate(source, maxsearch=1, locale='ads', diskroot=adsDIR):
    """ tabulate all files in arXiv sources, add basic file details
    """ 
    print 'query: % s' % source   

    bkeys = ['bibcode','eprintid']
    try:
        data = loadadsJSON(source, validate=False, tags=bkeys)
    except:
        print 'json file did not parse fully'
        print 'will now treat as XML'
        data = parseADSXML(source, bkeys)

    bibcodes = data.keys()
    print 'total bibcodes: %s' % len(bibcodes)
    files = []
    for bib in bibcodes[:maxsearch]:
        epid = pparXiv(data[bib]['eprintid'], auth='arXiv')
        datasets = []
        binfo = [bib, data[bib]['eprintid']]
        if epid != {}:
            wdir, sources = getSources(epid, 
                                       locale=locale,
                                       diskroot=diskroot)
            content = []
            data[bib]['sources'] = []
            for s in sources:
                f = os.path.join(wdir, s['file'])
                tcontent = processSource(f, 
                                         type=s['type'],
                                         encoding=s['encoding'],
                                         action='tlist')
                for t in tcontent:
                    finfo = []
                    finfo.extend(binfo)
                    for k in fkeys:
                        finfo.append(tagFormat(k,t,tagformats=fkey_formats))
                    files.append(dict(zip(bkeys+fkeys,finfo)))
        else:
            finfo = []
            finfo.extend(binfo)
            finfo.extend([None]*n_fkeys)
            files.append(dict(zip(fkeys,finfo)))
    return files 

arg_defs = {}
arg_defs['source'] = lambda x:os.path.exists(x) and x or None
arg_defs['outfile'] = lambda x:x != "" and x or "default" 
arg_defs['maxsearch'] = lambda x:x != "" and long(x) or 1L
arg_defs['indent'] = lambda x:x != "" and int(x) or None
arg_keys = ['source','outfile','maxsearch','indent']

def main(argv=None):
    """ main with sys.argv read and format
    """
    args = arg_keys
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
        argv[i] = arg_defs[arg](argv[i])

    argd = dict(zip(args,argv))
    
    if argd['source'] is None:
        raise Exception("no valid input file")

    data = _tabulate(source=argd['source'], maxsearch=argd['maxsearch'])
    with file(argd['outfile'],'w+') as f:
        json.dump(data, f, ensure_ascii=False,indent=argd['indent'])

if __name__ == "__main__":
    sys.exit(main())
