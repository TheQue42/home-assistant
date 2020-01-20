import copy
from enum import Enum, auto

"""
Route + Record-Route: <sip:10.10.1.11;lr>
Via: SIP/2.0/UDP 10.10.1.11:5060;branch=z9hG4bK41fa.6dd492f5e978dc144e4703d094e2ed91.0
Max-Forwards: 69
From: and To:
Call-ID: 9078dcaf53764deeb2a9f236660f8aab + CSeq: 22126 MESSAGE
Accept: + Allow
Supported, Require, Proxy-Require:
Content-Type: text/plain + Content-Length:    12
Contact:
Server, User-Agent: MicroSIP/3.19.10
Warning, P-hint:
Refer-To:

Parameters: q=1.0, ;tag ;branch, ;rport, ;received

Refer, Subscribe, Notify
"""


class GenericSipError(Exception):
    pass


class InvalidHeader(GenericSipError):
    pass


class ParameterExists(GenericSipError):
    pass


class HeaderType(Enum):
    CALL_ID = auto()
    TO = auto()
    FROM = auto()
    VIA = auto()
    CSEQ = auto()
    CONTACT = auto()
    WARNING = auto()
    ROUTE = auto()
    RECROUTE = auto()
    REFER_TO = auto()
    SUPPORTED = auto()
    ACCEPT = auto()
    SERVER = auto()
    USER_AGENT = auto()
    CUSTOM = auto()

    enumString = {CALL_ID: "Call-ID",
                    TO: "To",
                    FROM: "From",
                    VIA: "Via",
                    CSEQ: "CSeq",
                    CONTACT: "Contact",
                    WARNING: "Warning",
                    ROUTE: "Route",
                    RECROUTE: "Record-Route",
                    REFER_TO: "Refer-To",
                    SUPPORTED: "Supported",
                    ACCEPT: "Accept",
                    SERVER: "Server",
                    USER_AGENT: "User-Agent",
                    CUSTOM: "",
                    }


def text(htype: HeaderType) -> str:
    """

    :type htype: Enum
    """
    return HeaderType.enumString[htype]


### TODO: Define multiHeader, or SingleHeader to indicate maxNrOfCount.

class Header:
    __MAX_LEN__ = 1024

    # TODO: It would be simpler to indicate what we DO support but:
    # - line-folded headers
    # - escaping rules mania

    # GenericHeader: Value ;param1=Abc ;param2=xyz
    def __init__(self, *, htype: HeaderType, value: str, **kwargs):
        self._parameters = ""
        self.htype = htype
        self.value = value
        self.parameters = kwargs  # Param Names in .keys()

    def addParam(self, name: str, value: str, allow_update=False):
        # TODO Append multiple parameters
        if str in self.parameters.keys() or allow_update:
            raise ParameterExists
        self.parameters[name] = value

    def __str__(self) -> str:
        hName = text(self.htype)
        print(hName + ":" + str(self.value))

class CseqHeader(Header):

    def __init(self, method: str, number=-1):
        self.htype = HeaderType.CSEQ
        if number >= 0:
            number = str(random.randint(0, 2 ** 32 - 1))
        #self.value = method.upper() + " " + number
        super().__init__(htype=HeaderType.CSEQ, value=method.upper() + " " + number)


class NameAddress(Header):
    """Any header that contains a URI, with an optional display name, such as  From, To, Contact, Rec/Route:"""
    valid_list = (HeaderType.FROM,
                  HeaderType.TO,
                  HeaderType.ROUTE, HeaderType.RECROUTE,
                  HeaderType.CONTACT,
                  HeaderType.REFER_TO,
                  HeaderType.CUSTOM)

    def __init__(self, htype: HeaderType, uri: str, display_name="", **kwargs):

        if htype not in NameAddress.valid_list:
            raise GenericSipError

        if len(display_name) == 0:
            self.display_name = None
        else:
            # TODO: ONLY If display_name contains SPACE or "," add ""
            self.display_name = '"' + display_name + '"'

        # We're assuming that uri does NOT contain "<>"
        if not uri.find("sip:", 0, 4):
            uri = "sip:" + uri
        # TODO: Search for, and escape weird chars...
        self.uri = uri
        if len(kwargs.keys()) > 0:
            self.uri = "<" + self.uri +  ">"
        #self.parameters = kwargs  # Param Names in .keys()
        super().__init__(htype=htype,
                         value=self.display_name + " " + self.uri,
                         **kwargs)

    def setUri(self, uri : str):
        self.uri = uri
        # TODO: But now we need to re-generate in Base/Super::?


class CustomHeader(Header):

    def __init__(self, *, hname: str, value: str, **kwargs):
        self.hname = hname # Only custom, has to keep track of Header name as string.
        super().__init__(htype=HeaderType.CUSTOM, value=value, **kwargs)


class headerlist():

    def __init__(self):
        self.headerList = dict()

    def isAllowed(self, htype: HeaderType):
        # Check if duplicates are allowed.
        pass

    # headerList["Route"] = [Route-Uri1, Route-Uri2]
    # TODO: https://docs.python.org/2/library/collections.html#collections.defaultdict
    def add(self, htype: HeaderType, header : Header, addToTop=True):
        if htype not in self.headerList.keys():
            self.headerList[htype] = [header]
        else:
            if not addToTop:
                self.headerList[htype].append(header)
            else:
                self.headerList[htype].insert(header)


if __name__ == "__main__":
    h = headerlist()
    hh = NameAddress(HeaderType.FROM, uri="taisto@kenneth.qvist", display_name="Taisto k. Qvist", param1="pelle" )
    id(HeaderType)
    print(hh)