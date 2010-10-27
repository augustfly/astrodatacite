"""
this module provides functionality to obtain metadata for arxiv preprints

note: it should be taken care, not to make requests to arxiv in parallel from
  different processes on the same machine. otherwise, the machine might get
  blocked from arxiv. this may only happen, when the non-oai request is used,
  though.
"""
# $HeadURL$
# $LastChangedBy$
__version__ = "$LastChangedRevision$"

#
# notes:
# ------
# so far, arxiv puts a strange combination of text string in its oai exports:
# author names are somehow converted from latex to utf-8, but not in a 
# reversible way. titles on the other hand are lefts as they are - i.e. in
# latex format.
#

#
# test data:
# ----------
# hep-th/0208211
# - author with umlaut in name
# - additional dc:identifier element
#
# math-ph/0404037
# - tex in title
#

#-----------------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------------
# from standard python modules:
import urllib
import urlparse
import re
import time

# from third party packages:
try:
  #
  # if infrae's oai-pmh module is available, we use this instead of doing
  # the oai-pmh client stuff on our own.
  #
  import oaipmh
  SERVER_PROXY = oaipmh.ServerProxy('http://arXiv.org/oai2')
  oaipmh.register_oai_dc(SERVER_PROXY)
  
  # obtain info about arxiv oai sets, to compare potential arxiv ids against.
  # unfortunately this makes the import slow, because an oai request is
  # made.
  sets = map(lambda s: s[0], SERVER_PROXY.listSets()) 
  if not sets:
    raise ValueError
except:
  SERVER_PROXY = None
  
# from epubtk
from ePubTk.lib import xmllib
from ePubTk.lib.stringClasses import urlString

#-----------------------------------------------------------------------------
# globals:

# we want to keep track of '403 Forbidden' responses from arxiv, to avoid
# being blocked out. this is done on module level with a global status flag.
# obviously, nothing prevents us from reloading the module, to clear the flag.
# at latest at this point it should be taken care, to space http requests
# appropriately.
_ARXIV_HTTP_STATUS = 200

# exceptions:
ACCESS_DENIED = Exception("access to arxiv denied!")
INVALID_ID = Exception("invalid id!")
INCOMPLETE_NUMBER = Exception("incomplete number!")

# the 'official' arxiv domain:
NETLOC = "arXiv.org"

# alternative domains which will resolve to arxiv.org:
ALT_NETLOCS = ['arxiv.org', 'www.arxiv.org', 'xxx.arxiv.org', 
               'lanl.arxiv.org', 'xxx.lanl.gov']

#
# arxiv identifier patterns:
# --------------------------
# arxiv ids are made up of two parts, the (sub)group identifier and a number. 

# the following dictionary assigns patterns of subgroup
# identifiers (as used in ids) to group names.
if SERVER_PROXY:
  groups = []
  physicsFields = []
  
  for s in sets:
    comps = s.split(':')
    if comps[0] not in groups:
      groups.append(comps[0])
    if comps[0] == 'physics' and len(comps) == 2:
      physicsFields.append(comps[1])      
else:   
  # from arxiv oai repository sets as of april 2, 2005:
  physicsFields = ['nucl-ex',
                   'plasm-ph',
                   'supr-con',
                   'hep-ph',
                   'chem-ph',
                   'astro-ph',
                   'hep-ex',
                   'hep-lat',
                   'cond-mat',
                   'acc-phys',
                   'bayes-an',
                   'hep-th',
                   'mtrl-th',
                   'nucl-th',
                   'physics',
                   'quant-ph',
                   'math-ph',
                   'ao-sci',
                   'gr-qc',
                   'atom-ph']
  groups = ['physics', 'cs', 'math', 'nlin', 'q-bio']

_GROUP_PATTERNS = {'physics': '|'.join(map(lambda s: s.replace('-', '\-'), 
                                           physicsFields))}
for group in groups:
  if group != 'physics':
    _GROUP_PATTERNS[group] = group + '\.[A-Z]{2}'

# the number and version patterns are not group-specific:
_VERSION_PATTERN = "v[0-9]+"
_NUMBER_PATTERN = "[0-9]{1,7}"
NUMBER_LENGTH = 7

# group and number are separated by the following string:
_GROUP_NUMBER_SEPARATOR = '/'

# the following pattern can be used parse a candidate for an arxiv id from
# the path-component of an url:
_ID_PATTERN = "".join(["(%s)" % "|".join(_GROUP_PATTERNS.values()),
                       _GROUP_NUMBER_SEPARATOR,
                       "%s(%s)?" % (_NUMBER_PATTERN, _VERSION_PATTERN)])
PATH_PATTERN = re.compile("".join(["(/?(abs|ps|pdf|format))?",
                                   "/(?P<id>%s)" % _ID_PATTERN]))

# format for arxiv oai identifiers:
oaiIdentifier = lambda id: 'oai:%s:%s' % (NETLOC, id)

#-----------------------------------------------------------------------------
class ArxivUrl(urlString):
  """
  >>> ArxivUrl('http://xxx.lanl.gov/ps/hep-th/0208211').normalized()
  'http://arXiv.org/abs/hep-th/0208211'
  >>> ArxivUrl('http://arXiv.org/abs/hep-th/0208211').normalized()
  'http://arXiv.org/abs/hep-th/0208211'
  """
  def __init__(self, string):
    urlString.__init__(self, string)
    
    if self._loc.lower() in ALT_NETLOCS:
      m = PATH_PATTERN.match(self._path)
      if m:
        # ... and if so, normalize matching parts of URL
        self._id   = m.group('id')
        self._loc = NETLOC
            
        try:
          id = ArxivPreprint(self._id)
          self._path = id.canPath()
        except:
          self._path = 'abs/' + self._id
        return
      
    raise ValueError(string)

#-----------------------------------------------------------------------------
class ArxivPreprint(str):
  """
  class to access metadata of an arxiv preprint
  
  since arxiv preprints are identified by a unique string, we make this
  string the base of a class instance; thus derive this class from the C{str}
  class.
  
  >>> p = ArxivPreprint('hep-th/0208211')
  >>> p.authors() == TEST_AUTHORS
  1
  >>> str(p.title())
  'Perturbative Renormalization by Flow Equations'
  >>> p.url()
  'http://arXiv.org/abs/hep-th/0208211'
  >>> map(str, p.DCidentifiers())
  ['http://arxiv.org/abs/hep-th/0208211', 'Rev.Math.Phys. 15 (2003) 491']
  >>> p.number()
  '0208211'
  >>> p.group()
  'physics'
  >>> p.subGroup()
  'hep-th'
  >>> p = ArxivPreprint('math-ph/0404037')
  >>> assert re.sub('\s+', ' ', str(p.title())) == re.sub('\s+', ' ', TEST_TITLE)
  """
  def __init__(self, id):
    """
    pass the unique arxiv identifier as string in C{id}
    """
    # we store the different parts of the identifier ...
    self._group = None
    self._subGroup = None
    self._number = None
    
    # ... and also metadata we get via oai
    # note: the oai request is not sent upon initialization of an instance, 
    # but just when a method-call requires oai metadata.
    self._metadata = None
    
    # validate the identifier:
    try:
      id = str(id)
      parts = id.split(_GROUP_NUMBER_SEPARATOR)

      if len(parts) != 2:
        raise INVALID_ID

      for name, pattern in _GROUP_PATTERNS.iteritems():
        # add '$' to make sure we match the complete group-identifier part:
        if re.match('(%s)$' % pattern, parts[0]):
          self._group = name
          self._subGroup = parts[0]

      if self._group is None:
        raise INVALID_ID
      
      numberPattern = "(?P<number>%s)(?P<version>%s)?$" \
                    % (_NUMBER_PATTERN, _VERSION_PATTERN)
      m = re.match(numberPattern, parts[1])
      if not m:
        raise INVALID_ID
      
      if len(m.group('number')) != NUMBER_LENGTH:
        raise INCOMPLETE_NUMBER
      
      if m.group('version'):
        self._version = m.group('version')
      else:
        self._version = ''
        
      self._number = parts[1]
    except:
      raise
    
    return

  def _getContent(self, rec, term):
    return [xmllib.xpathGetText(e, '.') for e in\
            xmllib.xpath(rec, 
                         '//%s:%s' % (xmllib.DC_NS.prefix, term),
                         processorNss=((xmllib.DC_NS.prefix, xmllib.DC_NS.uri),))]
  
  def _getRecord(self):
    """
    get the oai metadata (if not already done)
    """
    if self._metadata is None:
      self.oaiRequest()
    

  def oaiRequest(self, mdPrefix='oai_dc'):
    """
    general oai interface to obtain xml-records for the preprint
    """    
    self._metadata = {}

    if SERVER_PROXY:
      res = SERVER_PROXY.getRecord(identifier=oaiIdentifier(self), 
                                   metadataPrefix=mdPrefix)
      if res[1]:
        self._metadata = res[1].getMap()
    else:
      query = urllib.urlencode({'verb': 'GetRecord',
                                'metadataPrefix': mdPrefix,
                                'identifier': oaiIdentifier(self)})
      url = urlparse.urlunsplit(('http', NETLOC, 'oai2', query, None))
      res = ArxivUrlOpener().open(url).read()
      self._metadata['creator'] = self._getContent(res, 'creator')
      self._metadata['title'] = self._getContent(res, 'title')
      self._metadata['identifier'] = self._getContent(res, 'identifier')
      
  
  #
  # functionality not relying on oai request:
  #
  def canPath(self):
    return "abs/" + self

  def group(self):
    return self._group
  
  def subGroup(self):
    return self._subGroup
  
  def number(self):
    return self._number
  
  def url(self):
    return "http://%s/%s" % (NETLOC, self.canPath())
  
  #
  # functionality requiring an oai request:
  #  
  def DCidentifiers(self):
    self._getRecord()
    return self._metadata.get('identifier', [])    
    #return self._identifiers

  def title(self):
    self._getRecord()
    if 'title' in self._metadata and self._metadata['title']:
      return self._metadata['title'][0]
  
  def authors(self):
    self._getRecord()
    return self._metadata.get('creator', [])

#-----------------------------------------------------------------------------
class ArxivUrlOpener(urllib.FancyURLopener):
  """
  we add a handler for 403 and 503 responses to the base class
  """
  def open(self, fullurl):
    """
    we open the url conditionally!
    """
    if _ARXIV_HTTP_STATUS != 200:
      raise ACCESS_DENIED
    
    return urllib.FancyURLopener.open(self, fullurl)      

  def http_error_503(self, url, fp, errcode, errmsg, headers, data=None):
    """
    if a 503 is returned as error code, we retry after the specified
    amount of time.
    """
    # determine the time to wait (passed as 'Retry-After' header) and wait 
    time.sleep(int(headers['Retry-After']))

    # then try to open again
    return self.open('http:' + url)
  
  def http_error_403(self, url, fp, errcode, errmsg, headers, data=None):
    """
    if a 403 is returned as error code, we set the global flag, to prevent
    subsequent requests to arxiv.
    """
    global ARXIV_HTTP_STATUS
    ARXIV_HTTP_STATUS = errcode
    return

#-----------------------------------------------------------------------------
# interfaces for doctest
#-----------------------------------------------------------------------------
TEST_NOTE = "note: tests require an internet connection!"
TEST_AUTHORS = [u'M\xfcller, Volkhard F.']
TEST_TITLE = 'Tensor operators and Wigner-Eckart theorem for the quantum superalgebra\n   U_{q}[osp(1\\mid 2)]'

def _test():
  import doctest, arxiv
  return doctest.testmod(arxiv)

if __name__ == "__main__":
  import sys
  print 'testing module %s' % sys.argv[0]
  print TEST_NOTE
  print "%s tests of %s failed." % _test()    
#--- last line ---------------------------------------------------------------
