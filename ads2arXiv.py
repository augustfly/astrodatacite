#!/usr/bin/env python

import os
import sys
import random
import tarfile
import tempfile
import time
import urllib
import pyparsing as pp

from datetime import datetime
from lxml import etree
from urlparse import urlparse
from arxiv import findRefType

xmlfile = 'query002.xml'
arxivroot = '/proj/adsduo/abstracts/sources/ArXiv/fulltext'

tagformats = {}
tagformats['eprintid'] = lambda x: x and x[0] or ''
tagformats['DOI'] = lambda x: x and x[0] or ''
tagformats['citations'] = lambda x: x and int(x[0]) or 0
tagformats['pubdate'] = lambda x: datetime.strptime(x[0], '%b %Y').date()
tagformats['author'] = lambda x: x and {'1st':x[0], 'N':len(x)} or {'1st':'', 'N':0}
tags = ['eprintid', 'DOI', 'citations', 'pubdate']

fsl = pp.Literal('/')
bsl = pp.Literal('\\')
hsh = pp.Literal('#')
lsb = pp.Literal('[')
rsb = pp.Literal(']')
lcb = pp.Literal('{')
rcb = pp.Literal('}')


class TeXCmd(object):
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

def tagFormat(tag, val):
    if tag in tagformats.keys():
        return tagformats[tag](val)
    else:
        return val

def ppTeXCmd(content, cmd='', opt_parser=None, req_parser=None,
             protect="./#:-\\", ret=''):
    """ use pyparsing...
        to parse a string stream for latex command(s)
        that hav the form:  \cmd[opt]{req} and return a
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
    """ pyparser for...
        ADS, FacilityID, PrivateID
        return parsed version
        protect: protect these symbols in the parse of the PrivateId
        auth: defaults to ADS
        the PrivateId is essentially a "URI" should/must follow the same rules.
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

def pparXiv(content):
    """ pyparser for dealing with old and new style classes of arXiv ids.
        returns various tidbits like year or volume

        : old-style    astro-ph/0703371
        : --------->   ['old','astro-ph','2007','0703371']
        : new-style    0712.2791
        : --------->   ['new','','0712','2791']
    """
    return

def ppBibCode(content):
    """ ADS bibcode parser
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
    tests = [['2009AJ....137....1F', '2009', 'AJ', '137', '', '1', 'F']]
    tests.append(['2001A&A...365L...1J', '2001', 'A&A', '365', 'L', '1', 'J'])
    tests.append(['1910YalRY...1....1E', '1910', 'YalRY', '1', '', '1', 'E'])
    tests.append(['1998bllp.confE...1U', '1998', 'bllp', 'conf', 'E', '1', 'U'])
    for test in tests:
        assert ppBibCode(test[0]) == tuple(test[1:])

def localSource(ref,type=type,root=arxivroot):
    """ given a local directory tree containing arXiv data, confirm the existance
        of a targeted arXiv data set/file/etc
    """
    #A:  type is a subdirectory under the root
    #A:  ref is a 
    return
    
def downloadSource(ref, type=type):
    """ Hacked from downloadSource in arXiv script version 0.2;
        Copyright 2008 Tom Brown
        Hacked 2010 August Muench
            do not gzip.

        actually this is entirely illegal:
            http://arxiv.org/robots.txt
                User-agent: *
                    Disallow: /e-print/
    """
#    downloadPath = os.path.expanduser(downloadPath)
#    filename = downloadPath + os.sep + ref.replace('/', '-') + ".tar"
    urlroot = 'http://arxiv.org/e-print/'
    urltarget = urlroot + ref
    print ' ' * 4 + '%-10s %s' % ('target url:', urltarget)
    urlresult = urllib.urlretrieve(urltarget)
    filename, httpobj = urlresult
    print ' ' * 4 + '%-10s %s' % ('output file:', filename)
    if not os.path.exists(filename): 
        print ' ' * 4 + '%-10s %s' % ('exists?', os.path.exists(filename))
        raise IOError('tarfile not downloaded', filename)
    return filename

def processSource(f, ext='tex', action='list', textfilter='begin{document}'):
    """ look in tarfile f for source files of extension ext; 
        return list of all content strings, one per file.
    """
    actions = ['list', 'read']
    action = action in actions and action or 'list'

    content = []
    try:
        tar = tarfile.open(f)    
        files = [n for n in tar.getnames() if n.split(os.extsep)[-1] == ext]
        print ' ' * 4 + '%-10s %s' % (ext + ' files:', len(files))
    
        if len(files) == 0:
            tar.close()
            return content
    
        for name in files:
            status = 'added'
            if action == 'list':
                content.append(name)
            elif action == 'read':
                try:
                    f = tar.extractfile(name)
                    fread = f.read()
                    f.close()
                    if fread.find(textfilter) != -1:
                        content.append(fread)
                    else:
                        status = 'ignored'
                except: 
                    raise
            print ' ' * 6 + '%-10s %s (%s)' % ('file:', name, status)
            tar.close()
    except Exception, e:
        if tarfile.is_tarfile(f):
            raise IOError('could not open tar file')
        else: 
            raise IOError('source is not a tar file')
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
                print ': %s' % f 
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
                print ': %s' % f 
                if not os.path.exists(f):
                    print ': does not exist'
                return (-1)
    return (0)
    
def parseADSXML(xml, tags=tags):
    """ parse some ADS XML references for specific tags
        return bibcode dict
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

def searchArXivSource(epid, cmd='dataset',
                      textfilter='begin{document}', tmpdir='/tmp'):
    """ for a given eprintid, download the source, search for tex filetypes
        filter on texfilter and search for commands cmd.
    """
    cmds = []
    ext = 'tex'
    try:
        etype, eref = findRefType(epid)
        print ' ' * 2 + 'eprint: %s (%s)' % (eref, etype) 
        #arxivsource = downloadSource(eref, etype) #, downloadPath=tmpdir)
        # 
        content = processSource(arxivsource, ext=ext,
                                textfilter=textfilter, action='read')
        if content != []:
            for page in content:
                cmds.extend(ppTeXCmd(content, cmd=cmd))
        print ' ' * 2 + 'number of "%s" codes: %s' % (cmd, len(cmds))
        for i, n in enumerate(cmds):
            print ' ' * 4 + '%i. %s' % (i + 1, n[1])
        cleanup = cleanupSource(tarball)
    except Exception, e:
        # should figure out why
        print 'searchArXivSource failed: %s' % e.args
    return cmds
  
    
def main(query=xmlfile, maxsearch=1, wait=(1, 1)):
    """ main
    """ 
    print 'query: %s' % query   
    data = parseADSXML(query, tags)
    tmpdir = tempfile.mkdtemp()

    bibcodes = data.keys()
    for bib in bibcodes[:maxsearch]:
        print 'starting %s' % bib
        epid = data[bib]['eprintid'].lower()
        datasets = []
        if epid != '':
            datasets = searchArXivSource(epid, cmd='dataset',
                                 textfilter='begin{document}', tmpdir=tmpdir)
        else:
            print 'no eprint'
        data[bib]['datasets'] = datasets
        w = random.uniform(wait[0] - wait[1], wait[0] + wait[1])
        print 'waiting %s seconds' % w
        time.sleep(w)
        print '\n'
    cleanup = cleanupSource(tmpdir)
    return data

if __name__ == "__main__":
    data = main()

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

dtex = ['ADS/Sa.CXO#obs/07338']
dtex.append('ADS/Sa.CXO\#obs/07338')
dtex.append('ADS/Sa.CXO\\#obs/07338%d3')

otex = ["\objectname[Name Orion Nebula Cluster]{Orion Nebula Cluster}"]
