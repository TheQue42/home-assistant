import copy
from enum import Enum, auto
import random


class GenericSipError(Exception):
    pass


class InvalidHeader(GenericSipError):
    pass


class ParameterExists(GenericSipError):
    pass


class HeaderEnum(Enum):
    CALL_ID = "Call-ID"
    TO = "To"
    FROM = "From"
    VIA = "Via"
    CSEQ = "CSeq"
    CONTACT = "Contact"
    ROUTE = "Route"
    RECROUTE = "Record-Route"
    REFER_TO = "Refer-To"
    EXPIRES = "Expires"
    SUPPORTED = "Supported"
    WARNING = "Warning"
    ACCEPT = "Accept"
    SERVER = "Server"
    SUBJECT = "Subject"
    USER_AGENT = "User-Agent"
    CUSTOM = ""

class MethodEnum(Enum):
    INVITE = "INVITE"
    CANCEL = "CANCEL"
    ACK = "ACK"
    BYE = "BYE"
    OPTIONS = "OPTIONS"
    REGISTER = "REGISTER"
    SUBSCRIBE = "SUBSCRIBE"
    PUBLISH = "PUBLISH"
    NOTIFY = "NOTIFY"
    REFER = "REFER"
    MESSAGE = "MESSAGE"

__VIA_MAGIC_COOKE = "z9hG4Bk"

### TODO: Define multiHeader, or SingleHeader to indicate maxNrOfCount.

class Header:
    __MAX_LEN__ = 1024

    # TODO: It would be simpler to indicate what we DO support but:
    # - line-folded headers
    # - escaping rules mania

    # GenericHeader: Value ;param1=Abc ;param2=xyz
    def __init__(self, *, htype: HeaderEnum, hvalues: dict(), **kwargs):
        self.htype = htype
        self.values = hvalues
        self.parameters = kwargs  # Param Names in .keys()

    def addParam(self, name: str, value: str, allow_update=False):
        # TODO Append multiple parameters, allowAppend=False
        if str in self.parameters.keys() or allow_update:
            raise ParameterExists
        self.parameters[name] = value

    def stringifyParameters(self) -> str:
        params = str()
        for paramKey in self.parameters.keys():
            params = params + " ;" + paramKey + "=" + str(self.parameters[paramKey])
        return params

    def __str__(self) -> str:
        #print("Using base-class __str__ for:", self.htype.value)
        hName = self.htype.value
        assert len(self.values.keys()) == 1
        keys = [key for key in self.values.keys()]
        value = self.values[keys[0]]
        return hName + ": " + str(value) + self.stringifyParameters()


class SimpleHeader(Header):

    def __init__(self, htype: HeaderEnum, hvalue: str, **kwargs):
        values = dict()
        values["0"] = hvalue
        super().__init__(htype=htype, hvalues=values, **kwargs)

    # NO overriding of __str__ here. Use base-class

class CseqHeader(Header):

    def __init__(self, method: MethodEnum, number=-1, **kwargs):
        if number >= 0:
            number = str(random.randint(0, 2 ** 32 - 1))
        values = {}
        values["method"] = method
        values["number"] = number
        super().__init__(htype=HeaderEnum.CSEQ, hvalues=values, **kwargs)  ### NOTE: We're sending the object..

    def __str__(self) -> str:
        hName = self.htype.value
        return hName + ": " +  self.values["method"].value.upper() + " " + str(self.values["number"]) + self.stringifyParameters()

# Proxy-Authorization: Digest username="goran",realm="ip-solutions.se",
# nonce="Ub8wuFG/L4xKkTQ5UwWt8/vkeVEuPWip",uri="sip:gabriel@ip-solutions.se",
# response="76ab7f721cfca9220ba071c038f83774",algorithm=MD5
class CustomHeader(Header):
    """"
    A Custom header can have one or more values. (But no editing currently)
    TODO: We need to decide if the keys of hvalues["cnonse"] = "skdjakjdk" should be used for anything
          or if we just ignore them as Accept: text/plain, text/html
    """
    def __init__(self, *, hname: str, value, **kwargs): # NOTE, value may be dict or string.
        self.hname = hname  # Only custom header has to keep track of Header name as string.
        if isinstance(value, dict):
            super().__init__(htype=HeaderEnum.CUSTOM, hvalues=value, **kwargs)
        if isinstance(value, str):
            values = dict()
            values["0"] = value
            super().__init__(htype=HeaderEnum.CUSTOM, hvalues=values, **kwargs)

    def __str__(self):
        hName = self.hname
        hValue = str()
        keyCount = len(self.values.keys())
        for i, val in enumerate(self.values.keys(), 1):
            hValue = hValue + self.values[val]
            if i < keyCount:
                hValue = hValue + ", "
        return hName + ": " +  hValue + self.stringifyParameters()


class NameAddress(Header):
    """Any header that contains a URI, with an optional display name, such as  From, To, Contact, Rec/Route:"""
    valid_list = (HeaderEnum.FROM,
                  HeaderEnum.TO,
                  HeaderEnum.ROUTE, HeaderEnum.RECROUTE,
                  HeaderEnum.CONTACT,
                  HeaderEnum.REFER_TO,
                  HeaderEnum.CUSTOM)

    def __init__(self, htype: HeaderEnum, uri: str, display_name="", **kwargs):

        if htype not in NameAddress.valid_list:
            raise GenericSipError

        values = {}
        values["uri"] = uri
        values["display_name"] = display_name
        super().__init__(htype=htype, hvalues=values, **kwargs)

    def __str__(self) -> str:
        hName = self.htype.value
        hValue = ""
        if len(self.values["display_name"]) == 0:
            display_name = None
        else:
            # TODO: ONLY If display_name contains SPACE or "," add ""
            hValue = '"' + self.values["display_name"] + '"' + " "

        # TODO: We're assuming that "incoming" uri does NOT contain "<>"
        if not self.values["uri"].find("sip:", 0, 4):
            uri = "sip:" + self.values["uri"]
        else:
            uri = self.values["uri"]
        # TODO: Search for, and escape weird chars...

        if len(self.parameters.keys()) > 0:
            uri = "<" + uri +  ">"

        hValue = hValue + uri
        return hName + ": " + hValue + self.stringifyParameters()

    def setUri(self, uri : str):
        self.values["uri"] = uri


class HeaderList:

    def __init__(self):
        self.headerList = dict()

    def isAllowed(self, htype: HeaderEnum):
        # Check if duplicates are allowed.
        pass

    # headerList["Route"] = [Route-Uri1, Route-Uri2]
    # TODO: https://docs.python.org/2/library/collections.html#collections.defaultdict
    def add(self, header : Header, addToTop=True):
        # TODO: Storing headers in dict/hash is maybe not so good, since it will change the order relative to how
        # they were added? It wont change inter-(same)-header order, so it shouldnt FAIL, but it still might feel
        # weird?
        htype = header.htype
        #print("Checking key: ", htype)
        if htype not in self.headerList.keys():
            #print("Adding: ", str(header))
            self.headerList[htype] = [header]
        else:
            if addToTop:
                self.headerList[htype].append(header)
            else:
                self.headerList[htype].insert(len(self.headerList[htype]), header)
            #print("Additional: ", len(self.headerList[htype]))

    def __str__(self) -> str:
        mHeaders = ""
        for hType in self.headerList.keys():
            for hInstance in self.headerList[hType]:
                mHeaders = mHeaders + str(hInstance)
                mHeaders = mHeaders + "\r\n"
        return mHeaders


if __name__ == "__main__":
    h = HeaderList()
    na1 = NameAddress(HeaderEnum.FROM, uri="taisto@kenneth.qvist", display_name="Taisto k. Qvist", param1="p1", param2="p2")
    na2 = NameAddress(HeaderEnum.FROM, uri="taisto@kenneth.qvist", param1="pelle")
    na3 = NameAddress(HeaderEnum.FROM, uri="taisto@kenneth.qvist")

    Cseq = CseqHeader(MethodEnum.INVITE, 5, cseqParam="Nej")

    subject1 = SimpleHeader(HeaderEnum.SUBJECT, "Subject-1", SubjectParam1=11212)
    subject2 = SimpleHeader(HeaderEnum.SUBJECT, "Subject-2", subjectParam2=222)

    custom1 = CustomHeader(hname="MyCustomHeader", value="MyCustomValue", customParam1="FortyTwo", X=0.1)
    vvv = dict()
    vvv["One"] = "realm=trippelsteg.se"
    vvv["Two"] = "digest"
    vvv["Three"] = "cnonce=9823139082013982"
#    print("Types:", type(vvv), type(vvv.keys()))

    custom2 = CustomHeader(hname="Authorization", value=vvv, customParam2="FortyThree", X=0.2)

    hlist = HeaderList()
    hlist.add(na1)
    hlist.add(na2)
    hlist.add(na3)
    hlist.add(Cseq)
    hlist.add(subject1)
    hlist.add(custom1)
    hlist.add(custom2)
    hlist.add(subject2)

    #print("vars:", vars(hlist))
    print("------------------")
    test = str(hlist)
    print(test)
