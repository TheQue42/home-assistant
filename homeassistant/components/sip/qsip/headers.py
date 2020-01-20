import copy
from enum import Enum, auto
import random
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

class HeaderEnum(Enum):
    CALL_ID = "Call-ID"
    TO = "To"
    FROM = "From"
    VIA = "Via"
    CSEQ = "CSeq"
    CONTACT = "Contact"
    WARNING = "Warning"
    ROUTE = "Route"
    RECROUTE = "Record-Route"
    REFER_TO = "Refer-To"
    SUPPORTED = "Supported"
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

### TODO: Define multiHeader, or SingleHeader to indicate maxNrOfCount.

class Header:
    __MAX_LEN__ = 1024

    # TODO: It would be simpler to indicate what we DO support but:
    # - line-folded headers
    # - escaping rules mania

    # GenericHeader: Value ;param1=Abc ;param2=xyz
    def __init__(self, htype: HeaderEnum, value: str, **kwargs):
        self.htype = htype
        self.value = value
        # TODO: Can we send None as value here, to make "rendering" the value later, performed by an inherited function?
        self.parameters = kwargs  # Param Names in .keys()

    def addParam(self, name: str, value: str, allow_update=False):
        # TODO Append multiple parameters
        if str in self.parameters.keys() or allow_update:
            raise ParameterExists
        self.parameters[name] = value

    def __str__(self) -> str:
        if self.htype != HeaderEnum.CUSTOM:
            hName = self.htype.value
        else:
            hName = self.hname
        return hName + ": " + str(self.value)

class CseqHeader(Header):

    def __init__(self, method: MethodEnum, number=-1):
        self.htype = HeaderEnum.CSEQ
        if number >= 0:
            number = str(random.randint(0, 2 ** 32 - 1))
        #self.value = method.upper() + " " + number
        super().__init__(HeaderEnum.CSEQ, value=method.value + " " + number)


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
        super().__init__(htype,
                         value=self.display_name + " " + self.uri,
                         **kwargs)

    def setUri(self, uri : str):
        self.uri = uri
        # TODO: But now we need to re-generate in Base/Super::?


class CustomHeader(Header):

    def __init__(self, *, hname: str, hvalue: str, **kwargs):
        self.hname = hname # Only custom, has to keep track of Header name as string.
        super().__init__(htype=HeaderEnum.CUSTOM, value=hvalue, **kwargs)


class headerlist():

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
                mHeaders = mHeaders + "\n"
                print("Adding", str(hInstance), len(str(hInstance)), " total: ", len(mHeaders))
        print("Finished:", len(mHeaders), type(mHeaders))
        return mHeaders


if __name__ == "__main__":
    h = headerlist()
    na = NameAddress(HeaderEnum.FROM, uri="taisto@kenneth.qvist", display_name="Taisto k. Qvist", param1="pelle" )

    Cseq = CseqHeader(MethodEnum.INVITE, 5)
    subject1 = Header(HeaderEnum.SUBJECT, "Super-Extension1")
    #print("vars:", vars(subject1))
    subject2 = Header(HeaderEnum.SUBJECT, "Super-Extension2")
    custom = CustomHeader(hname="MyCustomHeader", hvalue="MyCustomValue", param1="FortyTwo")

    hlist = headerlist()
    hlist.add(na)
    hlist.add(Cseq)
    hlist.add(subject1)
    hlist.add(custom)
    hlist.add(subject2)
    list = ["EEEE", "DDD", "CCCC", "BBBB", "AAA" ]
    mystring = str()
    for a in list:
        mystring = mystring + a
        print("String is: ", mystring)


    #print("vars:", vars(hlist))
    print("------------------")
    test = str(hlist)
    print("Test is:", test)