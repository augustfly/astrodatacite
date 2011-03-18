"""
    parse ADS XML references into json
    subset on "tags" list
"""

from ads_arXiv import adsXML2JSON, default_tags

import os, sys

defs = {}
defs['source'] = lambda x:os.path.exists(x) and x or None
defs['type'] = lambda x:x != "" and x or 'json'
defs['outfile'] = lambda x:x != "" and x or "default" 
defs['tags'] = lambda x:x != "" and x.split(',') or default_tags

def main(argv=None):
    convertto = ['json']
    args = ['source','type','outfile','tags']

    if argv == None:
        if sys.argv[1:] == []:
            print 'cmd variables are in order: ',args
            return
        argv = []
        argv.extend(sys.argv[1:])
        argv.extend(["","","",""])
        argv = argv[:4]

    for i,arg in enumerate(args):
        argv[i] = defs[arg](argv[i])

    argd = dict(zip(args,argv))
    
    if argd['source'] is None:
        raise Exception("no valid input file")
    
    if argd['type'] not in convertto:
        raise Exception("invalid conversion type")

    if argd['outfile'] == 'default':
        argd['outfile'] = os.path.splitext(argd['source'])[0]+'.'+argd['type']

    print 'executing conversion of %s to format %s as %s' % (argd['source'],argd['type'],argd['outfile'])
    print 'the following tags are to be extracted',argd['tags']

    #tags = default_tags
    if argd['type'] == 'json':
       adsXML2JSON(argd['source'], argd['tags'], argd['outfile'])

    return

if __name__ == "__main__":
    sys.exit(main())
