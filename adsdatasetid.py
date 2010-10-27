
import urlparse
from urllib import URLopener
from xml.etree import ElementTree as etree

facilities_file = 'http://vo.ads.harvard.edu/dv/facilities.txt'
profiles_file = 'http://vo.ads.harvard.edu/dv/admin/profiles.xml'

def get_facilities(file):
    o = URLopener().open(file)
    t = o.readlines()
    o.close()
    return [i.split(' ')[0].lower() for i in t]

def get_profiles(xml):
    o = URLopener().open(xml)
    ftree = etree.parse(o)
    items = ftree.getroot().getchildren()
    tags = [a.tag for a in items[0].getchildren()]
    profiledict = dict()
    ids = [item.findtext('id') for item in items]
    for item in items:
        itemdict = dict()
        for tag in tags:
              if tag != 'facilities' and  item.find(tag) is not None:
                     itemdict[tag] = item.find(tag).text
              elif tag == 'facilities':
                     itemdict[tag] = [fac.text for fac in
                                      item.findall('facilities/item')]

        profiledict[itemdict['id']] = itemdict
    return profiledict

class ADSExceptions(object):
    """ Capture some likely static kinds of exceptions for 
        specialized responses when dataaset ID belches
    """
    class BadAuthorityId(Exception):
        def __init__(self, good, bad):
            self.good = good
            self.bad = bad

        def __str__(self):
            message = "Bad Authority Id in identifier: %s must be %s" % (self.bad, self.good)
            return message

    class InvalidFacilityId(Exception):
        def __init__(self, bad):
            self.bad = bad

        def __str__(self):
            message = "Facility ID %s not in known list" % self.bad
            return message

    class UnparsableURI(Exception):
        def __init__(self, bad):
            self.bad = bad

        def __str__(self):
            message = "The dataset ID is not parseable as %s" % self.bad
            return message


class DatasetID(object):
    """ Container package for parsing and validating ADS Dataset ID URN
    """
    urischeme = "ivo"
    AuthorityId = "ADS"
    FacilityID = ""
    PrivateID = ""

    _ParseResult = urlparse.ParseResult

    facilities = get_facilities(facilities_file)
    profiles = get_profiles(profiles_file)

    urlparse.uses_netloc.append(urischeme)
    urlparse.uses_fragment.append(urischeme)

    def __init__(self, datasetid=None):
        if datasetid is not None:
           self.AuthorityId, self.FacilityId, self.PrivateId = \
                self.parse_id(datasetid, urischeme=self.urischeme)

    def __call__(self, call=None, update=False):
        """ My way of reinitializing an object with anew init
        """
        if call is None:
            return self._geturl()
        if update:
           self.AuthorityId, self.FacilityId, self.PrivateId = \
                self.parse_id(call, urischeme=self.urischeme)
        else:
            return self.parse_id(call, urischeme=self.urischeme)

    def __str__(self):
        return self._geturl()

    def _fragments(self, fragment=None):
        fragment = fragment or self.PrivateId or '/'
        return fragment.split('/')

    def _geturl(self):
        return self._ParseResult(self.urischeme, self.AuthorityId,
                         self.FacilityId, '', '',
                         self.PrivateId).geturl()

    def parse_id(self, datasetid, urischeme=urischeme):
        """ Parse (and validate) the dataset ID (by converting it to an URI) 
            Test each portion according to some static rules.
        """
        try:
            parsed = urlparse.urlparse(urischeme + "://" + datasetid)
        except:
            raise ADSExceptions.UnparsableURI(urischeme + "://" + datasetid)

        try:
            assert parsed.netloc.upper() == self.AuthorityId.upper()
        except:
            raise ADSExceptions.BadAuthorityId(self.AuthorityId.upper(),
                                               parsed.netloc.upper())
        AuthorityId = self.AuthorityId

        try:
            assert parsed.path[1:].lower() in self.facilities
        except:
            raise ADSExceptions.InvalidFacilityId(parsed.path[1:])
        FacilityId = parsed.path[1:]
        PrivateId = parsed.fragment

        return AuthorityId, FacilityId, PrivateId

    def broker_id(self):
        """ Stub
            Check existence of dataset via ADS broker
        """
        pass

    def linked_data(self):
        """ Stub
            Return Linked data version of URI
        """
        pass

class PrivateID(object):
    def __init__(self, id=None):
        pass




