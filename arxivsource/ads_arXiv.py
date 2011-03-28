"""
    library of ads/arXiv tools
"""

import os
import sys
import gzip
import json
import random
import tarfile
import tempfile
import time
import urllib
import mimetypes as mime
import pyparsing as pp

from datetime import datetime
from glob import glob1 as glob
from lxml import etree
from urlparse import urlparse


adsDIR = '/proj/adsduo/abstracts/sources/ArXiv/fulltext'
#adsDIR = '../../../Data/astrodatacite/ADS'
arXivURL = 'http://arxiv.org/e-print/'
arXivArchives = ['astro-ph', 'cond-mat', 'gr-qc', 'hep-ex', 'hep-lat',
                 'hep-ph', 'hep-th', 'math-ph', 'nucl-ex', 'nucl-th',
                 'physics', 'quant-ph', 'math', 'nlin', 'cs', 'q-bio',
                 'q-fin', 'stat']

default_tags = ['eprintid', 'DOI', 'citations', 'pubdate']
tagformats = {}
tagformats['eprintid'] = lambda x: x and x[0] or None
tagformats['DOI'] = lambda x: x and x[0] or None
tagformats['citations'] = lambda x: x and int(x[0]) or 0
tagformats['pubdate'] = lambda x: datetime.strptime(x[0], '%b %Y').date()
tagformats['author'] = lambda x: x and {'1st':x[0], 'N':len(x)} or {'1st':'', 'N':0}

fsl = pp.Literal('/')
bsl = pp.Literal('\\')
hsh = pp.Literal('#')
lsb = pp.Literal('[')
rsb = pp.Literal(']')
lcb = pp.Literal('{')
rcb = pp.Literal('}')

class TeXCmd(object):
    """ class container for LaTeX commands
    """
    cmd = 'begin'
    opt = ''
    req = 'document'
    def __init__(self, **kwargs):
        for key, val in kwargs.items():
            if hasattr(self, key): setattr(self, key, val)
            
    def __call__(self):
        return '\\' + self.cmd + '[' + self.opt + ']' + '{' + self.req + '}'
    
#def query(template):
#    parsed = urlparse(template)
#    return parsed.query

def _postarXivAction(s, loc, tok):
    """ take a pyparsing element from pparXiv and do some stuff to it.
        override this function to get other kinds of parameters from
        the parsing of the arXiv ID.  This version does:
        
        : adds "issue" key (short year+month)
        : checks for "version"; adds '1' if not defined
        : adds "id"
        : adds "adspath" key, a relative directory path for source from ADS
        : adds the parsed arXiv id to the key 'eprintid'.
    """
    # create "issue"
    tok['issue'] = tok['year'] + tok['month']
    
    # check for version
    if tok.get('version') == None:
        tok['version'] = '1'
    
    # various useful things.    
    if tok['scheme'] == 'old':
        tok['id'] = tok['archive'] + '/' + tok['issue'] + tok['number']
        tok['adspath'] = os.path.join(*[tok.get(k) 
                        for k in ['archive', 'fullyear']])
        tok['adssrc'] = tok['issue']+tok['number']
    else:
        tok['id'] = tok['issue'] + "." + tok['number']
        tok['adspath'] = os.path.join(*[tok.get(k) 
                        for k in ['server', 'issue']])
        tok['adssrc'] = tok['number']
    tok['eprintid'] = s

def tagFormat(tag, val, tagformats=tagformats):
    """ function to format input val according to keyed dictionary
        of lambda functions, "tagformats"
    """
    if tag in tagformats.keys():
        return tagformats[tag](val)
    else:
        return val

def parseADSXML(xml, tags=default_tags):
    """ parse ADS XML references for specific tags
        return bibcode dict.
        
        required dealing with unkeyed namespaces
    """
    keytag = 'bibcode'
    tree = etree.parse(xml)
    root = tree.getroot()
    
    xmlns = root.nsmap
    if xmlns.has_key(None):
        nsurl = xmlns[None]
        nsnew = urlparse(xmlns[None]).path.split('/')[-1]
        if nsnew == '': nsnew = 'dummy'
        xmlns[nsnew] = nsurl
        xmlns.pop(None)
        
    records = tree.xpath('//references:record', namespaces=xmlns)
    
    data = {}
    for record in records:
        b = record.xpath('references:%s/text()' % keytag, namespaces=xmlns)[0]
        vals = []
        for tag in tags:
            val = record.xpath('references:%s/text()' % tag, namespaces=xmlns)
            vals.append(tagFormat(tag, val))
        data[b] = dict(zip(tags, vals))

    print 'Number of records: %s\n' % len(records)
    return data

def adsXML2JSON(source, tags=default_tags, outfile=None):
    """
        try to pre-parse the ADS xml files and cache some data as json
    """
    def handler(obj):
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        #elif isinstance(obj, ...):
        #    return ...
        else:
            raise TypeError, 'Object of type %s with value of %s is not JSON serializable' % (type(obj), repr(obj))

    outfile = outfile or os.path.splitext(source)[0]+".json"
    data = parseADSXML(source,tags=tags)
    with file(outfile,'w+') as f:
        json.dump(data, f, ensure_ascii=False,default=handler)

def loadadsJSON(source, validate=True, tags=default_tags):
    """
        load the cached json version of the ads references.
        return the dictionary.
        validate that the loaded object contains the correct keys in "tags"
    """
    with file(source,'r') as f:
        j = json.load(f)
    
    if validate:
        jtags = j.values()[0].keys()
        for tag in tags:
            try:
                assert tag in jtags
            except:
                print 'json does not contain all necessary tags. recache source'
                return {}
    return j


def ppTeXCmd(content, cmd='', opt_parser=None, req_parser=None,
             protect="./#:-\\", ret=''):
    """ latex command pypaser

        Parse a string stream for latex command(s)
        that have the form:  \cmd[opt]{req} and return a
        list of triple tuples of (cmd,opt,req)
        
        always act like content is to be scanned.
        returns lists of tuples of cmd,opt,req values.
        
        todo:
            * should allow for spaces in the opt,req strings;
            * add opt_parser, req_parser options
            * might check cmd for valid TeX cmd.
            * might add output options.
    """
    bsl = "\\"
    cmd_gram = pp.alphas
    
    if cmd == '':
        cmd = pp.Word(cmd_gram)
    elif cmd[0] == bsl:
        cmd = pp.Literal(cmd[1:])
    else:
        cmd = pp.Literal(cmd)
    cmd = cmd.setResultsName("cmd")
    
    opt_gram = pp.alphanums + protect
    opt_word = pp.Word(opt_gram).setResultsName("opt")
    
    # this could be any text. add a space?
    req_gram = pp.alphanums + protect + ' '
    req_word = pp.Word(req_gram).setResultsName("req")
    
    TeXp = bsl + cmd + pp.Optional("[" + opt_word + "]") + "{" + req_word + "}"
    
    try:
        pTeX = TeXp.scanString(content)
    except:
        return
    return [(p.cmd, p.opt, p.req) for p, s, e in pTeX]

def ppDataSetID(content, protect='. / -', auth='ADS'):
    """ ADS DataSetID pyparser
        
        See:
        Grammar has three elements: ADS, FacilityID, PrivateID
        return parsed version as tuple
        
        protect: protect these symbols in the parse of the PrivateId
        auth: defaults to ADS
        
        the PrivateId is essentially a "URI" and
        should/must follow the same rules.
    """
    AuthorityId = pp.Literal(auth).setResultsName("AuthorityId")
    
    # a "period" is the only none alphanum character acceptable.
    fac_gram = pp.alphanums + '.'
    FacilityId = pp.Word(fac_gram).setResultsName("FacilityId")
    
    # allow the call to pass values to protect
    pri_gram = pp.alphanums + protect
    PrivateId = pp.Word(pri_gram).setResultsName("PrivateId")
    
    # splitter could be written a few ways
    Splitter = pp.Optional(pp.Suppress(pp.Literal('\\'))) + pp.Literal('#')
    DataSetIDp = AuthorityId + "/" + FacilityId + Splitter + PrivateId
    DataSetIDp.errmsg = 'Failed to Parse DatasetID'
    
    try:
        pDataSetId = DataSetIDp.parseString(content)
    except:
        return
    return pDataSetId.AuthorityId, pDataSetId.FacilityId, pDataSetId.PrivateId

def pparXiv(content, auth='arXiv'):
    """ arXiv ID pyparser
        
        Written to deal with old and new style classes of arXiv ids
        (before and after 1 April 2007)
        
        : old-scheme    arXiv:astro-ph/0703371
        : new-scheme    arXiv:0712.2791

        arXiv id's may consist only of the root element as given above
        or they may have a number of other optional words:
        
        : new-scheme    arXiv:0712.2791v1
        : old-scheme    arXiv:math.GT/030936
        
        The main issues are these:
        
        1. ADS does not use version numbers in eprint IDs;
        2. the "subject" class is not part of any URL link structure
        3. Citations may include the subject class.
        
        Here is my attempt at the BNF Grammar for the arXiv IDs
        
        preprint ::= <auth>:<epid>
        <auth>   ::= 'arXiv' | ...
        <epid>   ::= <new> | <old>

        <old>    ::= <archive>/<year><month><oldart>
        <new>    ::= <year><month>.<newart>

        <archive>::= OneOf('astro-ph' | 'physics' | 'q-bio' | 'cs' .... )

        <year>   ::= pp.nums * 2
        <month>  ::= pp.nums * 2 

        <oldart> ::= pp.nums * 3
        <newart> ::= pp.nums * 4

        Conversion actions for the Grammar include:

        <fullyear> ::= <mc><year>
        <mc>       ::= pp.nums * 2
        <mc>       ::= <year> > 91 -> 19
        <mc>       ::= <year> > 00 -> 20

    """
    server = pp.Literal(auth).setResultsName("server")

    year = pp.Word(pp.nums, exact=2).setResultsName("year")
    year.addParseAction(lambda tok: tok.__setitem__('fullyear',
                        int(tok[0]) > 91 and '19' + tok[0] or '20' + tok[0]))  
    month = pp.Word(pp.nums, exact=2).setResultsName("month")

    archive = pp.oneOf(arXivArchives).setResultsName('archive')
    subject = pp.Optional(pp.Literal(".") + 
              pp.Word(pp.alphas, exact=2).setResultsName('subjectclass'))

    newart = pp.Word(pp.nums, exact=4).setResultsName('number')
    oldart = pp.Word(pp.nums, exact=3).setResultsName('number')

    version = pp.Optional(pp.Literal('v') + \
              pp.Word(pp.nums, exact=1).setResultsName('version'))

    oldscheme = archive + subject + pp.Suppress('/') + year + month + oldart
    newscheme = year + month + pp.Suppress(".") + newart

    oldscheme.addParseAction(lambda tok: tok.__setitem__('scheme', 'old'))
    newscheme.addParseAction(lambda tok: tok.__setitem__('scheme', 'new'))

    preprint = server + pp.Suppress(":") + (oldscheme | newscheme) + version
    preprint.addParseAction(_postarXivAction)

    try:
        return preprint.parseString(content).asDict()
    except:
        return {}

def testpparXiv():
    """ test function for parsing arXiv id versions
    """
    tests = [['arXiv:astro-ph/0703371', 'old', 'astro-ph', '07', '03', '371']]
    tests.append(['arXiv:0712.2791', 'new', None, '07', '12', '2791'])
    for test in tests:
        assert pparXiv(test[0]).asList() == test[1:] #will not work

def ppBibCode(content):
    """ ADS bibcode parser
        
        See:
        
        Grammar:
            YYYYJJJJJVVVVMPPPPA
    """
    y_grm = pp.nums
    j_grm = pp.alphas + '.&'
    v_grm = pp.alphanums + '.'
    m_grm = "iDELPQRSTUV" + '.' # restricting this is prob a bad idea
    p_grm = pp.alphanums + '.'
    a_grm = pp.alphas + '.'
    
    noper = lambda t: [x.replace('.', '') for x in t]
    
    y = pp.Word(y_grm, exact=4).setResultsName('Y')
    j = pp.Word(j_grm, exact=5).setResultsName('J')
    j.setParseAction(noper)
    v = pp.Word(v_grm, exact=4).setResultsName('V')
    v.setParseAction(noper)
    m = pp.Word(m_grm, exact=1).setResultsName('M')
    m.setParseAction(noper)
    p = pp.Word(p_grm, exact=4).setResultsName('P')
    p.setParseAction(noper)
    a = pp.Word(a_grm, exact=1).setResultsName('A')
    a.setParseAction(noper)
    bibp = y + j + v + m + p + a
    bib = bibp.parseString(content)
    return (bib.Y, bib.J, bib.V, bib.M, bib.P, bib.A)

def testppBibCode():
    """ test function for bibcode parser
    """
    tests = [['2009AJ....137....1F', '2009', 'AJ', '137', '', '1', 'F']]
    tests.append(['2001A&A...365L...1J', '2001', 'A&A', '365', 'L', '1', 'J'])
    tests.append(['1910YalRY...1....1E', '1910', 'YalRY', '1', '', '1', 'E'])
    tests.append(['1998bllp.confE...1U', '1998', 'bllp', 'conf', 'E', '1', 'U'])
    for test in tests:
        assert ppBibCode(test[0]) == tuple(test[1:])

def getSources(epid, locale='ads',
                 diskroot=adsDIR, urlroot=arXivURL):
    """ given a reference and a locale, 
        return the path to the source, 
        downloading it as necessary.
    """
    #A:  type is a subdirectory under the root
    #A:  ref is a
    locales = ['ads','disk', 'url']
    locale = locale in locales and locale or 'disk'
    
    wdir = ''
    wfiles = []
    wnames = ('file', 'type', 'encoding')
    if locale == 'ads':
        wdir = os.path.abspath(os.path.join(diskroot, epid['adspath']))
        wfiles = [dict(
                       zip(wnames,
                           (g,) + mime.guess_type(g))) 
                  for g in glob(wdir, '*' + epid['adssrc'] + '.*')]
    else:
        wdir = tempfile.mkdtemp()
        wfiles = ['foobar']
#         urlroot = 'http://arxiv.org/e-print/'
#         urltarget = urlroot + ref
#         print ' ' * 4 + '%-10s %s' % ('target url:', urltarget)
#         urlresult = urllib.urlretrieve(urltarget)
#         filename, httpobj = urlresult
#         print ' ' * 4 + '%-10s %s' % ('output file:', filename)
#         if not os.path.exists(filename): 
#             print ' ' * 4 + '%-10s %s' % ('exists?', os.path.exists(filename))
#             raise IOError('tarfile not downloaded', filename)
        
    return wdir, wfiles
    
# def downloadSource(ref, type=type):
#     """ Hacked from downloadSource in arXiv script version 0.2;
#         Copyright 2008 Tom Brown
#         Hacked 2010 August Muench
#             do not gzip.
# 
#         actually this is entirely illegal:
#             http://arxiv.org/robots.txt
#                 User-agent: *
#                     Disallow: /e-print/
#     """
# #    downloadPath = os.path.expanduser(downloadPath)
# #    filename = downloadPath + os.sep + ref.replace('/', '-') + ".tar"
#     urlroot = 'http://arxiv.org/e-print/'
#     urltarget = urlroot + ref
#     print ' ' * 4 + '%-10s %s' % ('target url:', urltarget)
#     urlresult = urllib.urlretrieve(urltarget)
#     filename, httpobj = urlresult
#     print ' ' * 4 + '%-10s %s' % ('output file:', filename)
#     if not os.path.exists(filename): 
#         print ' ' * 4 + '%-10s %s' % ('exists?', os.path.exists(filename))
#         raise IOError('tarfile not downloaded', filename)
#     return filename

def processSource(s, type='application/x-tar', encoding=None, action='list',
                  filefilter=['application/x-tex'], textfilter=''):
    """ process whatever source file is provided for a paper into one of three forms
        "action" => return one of:
           [tlist] list of all files in s
           [list]  list of files in s filtered on file extension
           [read]  string content of filtered files in s
    """
    actions = ['tlist', 'list', 'read']
    content = []
    processable = ['application/x-tex', 'application/x-tar', 'text/plain']

    status = 'processing'
    if type not in processable:
        status = 'not processable' 
        print ' ' * 2 + ' % -10s % s (% s)' % ('source:', s, status)
        return content
    else:
        print ' ' * 2 + ' % -10s % s (% s)' % ('source:', s, status)
        
    action = action in actions and action or 'list'

    if type == 'application/x-tar':
        try:
            tar = tarfile.open(s)    
            tlist = tar.getnames()
            files = [n for n in tlist
                     if mime.guess_type(n)[0] in filefilter]
        
            if len(files) == 0:
                tar.close()
                return content

            if action == 'tlist':
                tar.close()
                return tlist
        
            print ' ' * 4 + ' % -10s % s' % ('filtered files:', len(files))
            for name in files:
                status = 'added'
                if action == 'list':
                    content.append(name)
                elif action == 'read':
                    try:
                        f = tar.extractfile(name)
                        fread = f.read()
                        f.close()
                        if fread.count(textfilter) != 0:
                            content.append(fread)
                        else:
                            status = 'ignored'
                    except: 
                        raise
                print ' ' * 6 + ' % -10s % s (% s)' % ('file:', name, status)
            tar.close()
        except Exception, e:
            print ' ' * 4 + ' %-10s %s' % ('could not open', s)
            print ' ' * 6 + ' %-10s %s' % ('error:', e)
            #if tarfile.is_tarfile(s):
                #raise IOError('could not open tar file: ' + s)
            #else: 
                #raise IOError('source is not a tar file: ' + s)
                #print ' ' * 4 + ' %-10s %s' % ('not a tarfile',s)
    else:
        status = 'added'
        name = os.path.basename(not encoding and s or os.path.splitext(s)[0])
        if action == 'tlist':
            content.append(name)
            return content
        if mime.guess_type(name) not in filefilter: 
            return content
        if action == 'list':
            content.append(name)
        elif action == 'read':
            try:
                if encoding == 'gzip':
                    f = gzip.open(s)
                else:
                    f = open(s)
                fread = f.read()
                f.close()
                if fread.count(textfilter) != 0:
                    content.append(fread)
                else:
                    status = 'ignored'
            except: 
                raise
        print ' ' * 6 + ' % -10s % s (% s)' % ('file:', name, status)                 
    return content

def cleanupSource(f):
    """ delete f 
        add checks if f is dir or file. 
        run os.[rmdir,remove] appropriately.
    """
    if os.path.exists(f):
        if os.path.isdir(f):
            try:
                os.rmdir(f)
            except:
                # either its not in existence or its not empty
                print ': the directory'
                print ': % s' % f 
                if os.listdir(f) != []:
                    print ': is not empty'
                else:
                    print ': does not exist'
                return (-1)
        elif os.path.isfile(f):
            try:
                os.remove(f)
            except:
                print ': the file'
                print ': % s' % f 
                if not os.path.exists(f):
                    print ': does not exist'
                return (-1)
    return (0)
    
def searchSource(content, cmd='dataset'):
    """ parse a string for TeX cmds
    """
    cmds = []
    if content != []:
        for page in content:
            cmds.extend(ppTeXCmd(page, cmd=cmd))
        print ' ' * 2 + 'number of "%s" codes: % s' % (cmd, len(cmds))
        for i, n in enumerate(cmds):
            print ' ' * 4 + ' % i. % s' % (i + 1, n[1])
    return cmds
  

# testing tools
tquery = "http://adsabs.harvard.edu/cgi-bin/nph-abs_connect?db_key=AST&db_key=PRE&qform=AST&arxiv_sel=astro-ph&arxiv_sel=cs&arxiv_sel=physics&sim_query=YES&ned_query=YES&adsobj_query=YES&aut_logic=OR&obj_logic=OR&author=&object=&start_mon=5&start_year=2010&end_mon=6&end_year=2010&ttl_logic=OR&title=&txt_logic=OR&text=&nr_to_return=500&start_nr=1&article_sel=YES&jou_pick=NO&ref_stems=AJ...,ApJ..,ApJS.&data_and=ALL&preprint_link=YES&group_and=ALL&start_entry_day=&start_entry_mon=&start_entry_year=&end_entry_day=&end_entry_mon=&end_entry_year=&min_score=&sort=ODATE&data_type=SHORT_XML&aut_syn=YES&ttl_syn=YES&txt_syn=YES&aut_wt=1.0&obj_wt=1.0&ttl_wt=0.3&txt_wt=3.0&aut_wgt=YES&obj_wgt=YES&ttl_wgt=YES&txt_wgt=YES&ttl_sco=YES&txt_sco=YES&version=1"

ttex = []
ttex.append("Our census has expanded the confirmed boundaries of IC~348  to a physical size comparable to that well studied portion of the \objectname[Name Orion Nebula Cluster]{Orion Nebula Cluster} \citep{1998ApJ...492..540H}.\n\n Paper I contains all details of the  data processing except for the far-infrared Multiband Imaging Photometer for \sst\ \citep[\mips;][]{2004ApJS..154...25R} observations  (see \S\\ref{sec:select:mips})\\footnote{The \sst\ data obtained for this paper were taken from AORs~\dataset[ADS/Sa.Spitzer#3955200]{3955200}, \dataset[ADS/Sa.Spitzer#3651584]{3651584}, \dataset[ADS/Sa.Spitzer#4315904]{4315904}.}.")
ttex.append("\section{OBSERVATIONS AND DATA REDUCTION}\n\label{s2}\n Deep Chandra observations of Kes 75 were carried out on Jun 5-12, 2006 in four exposures (Observation IDs [ObsIDs] \dataset [ADS/Sa.CXO#obs/06686] {6686}, \dataset [ADS/Sa.CXO#obs/07337] {7337}, \dataset [ADS/Sa.CXO#obs/07338] {7338} \& \dataset [ADS/Sa.CXO#obs/07339] {7339}) which began 7 days after the first four bursts that were reported by \citet{gav08}, and 50 days before the fifth one.")

stex = ["\dataset[ADS/Sa.CXO#obs/07338]{ObsID 7338}"]
stex.append("\dataset [ADS/Sa.CXO#obs/07338] {ObsID 7338}")
stex.append("\dataset [ADS/Sa.CXO#obs/07338] {ObsID 7338}")
stex.append("(\dataset[ADS/Sa.CXO\#obs/07338]\n{ObsID 7338})")
stex.append("(\dataset[ADS/Sa.CXO\#obs/07338]\\n{ObsID 7338})")

dtex = ['ADS / Sa.CXO#obs/07338']
dtex.append('ADS/Sa.CXO\#obs/07338')
dtex.append('ADS/Sa.CXO\\#obs/07338%d3')

otex = ["\objectname[Name Orion Nebula Cluster]{Orion Nebula Cluster}"]

