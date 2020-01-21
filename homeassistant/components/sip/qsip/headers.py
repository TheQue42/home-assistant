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
    def __init__(self, htype: HeaderEnum, value: str, **kwargs):
        self.htype = htype
        self.value = value
        # TODO: Can we send None as value here, to make "rendering" the value later, performed by an inherited function?
        self.parameters = kwargs  # Param Names in .keys()

    def addParam(self, name: str, value: str, allow_update=False):
        # TODO Append multiple parameters, allowAppend=False
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
        if self.display_name is not None:
            display_name = self.display_name + " "
        else:
            display_name = ""
        super().__init__(htype,
                         value=display_name + self.uri,
                         **kwargs)

    def setUri(self, uri : str):
        self.uri = uri
        # TODO: But now we need to re-generate in Base/Super::?


class CustomHeader(Header):

    def __init__(self, *, hname: str, hvalue: str, **kwargs):
        self.hname = hname # Only custom, has to keep track of Header name as string.
        super().__init__(htype=HeaderEnum.CUSTOM, value=hvalue, **kwargs)


class HeaderList():

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
                params = str()
                for paramKey in hInstance.parameters.keys():
                    params = params + " ;" + paramKey + "=" + str(hInstance.parameters[paramKey])
                mHeaders = mHeaders + str(hInstance) + params

                mHeaders = mHeaders + "\r\n"
                #print("Adding", str(hInstance), len(str(hInstance)), " total: ", len(mHeaders))
        #print("Finished:", len(mHeaders), type(mHeaders))
        return mHeaders


if __name__ == "__main__":
    h = HeaderList()
    na1 = NameAddress(HeaderEnum.FROM, uri="taisto@kenneth.qvist", display_name="Taisto k. Qvist", param1="pelle")
    na2 = NameAddress(HeaderEnum.FROM, uri="taisto@kenneth.qvist", param1="pelle")
    na3 = NameAddress(HeaderEnum.FROM, uri="taisto@kenneth.qvist")
    Cseq = CseqHeader(MethodEnum.INVITE, 5)
    subject1 = Header(HeaderEnum.SUBJECT, "Super-Extension1", hisesea=11212)
    #print("vars:", vars(subject1))
    subject2 = Header(HeaderEnum.SUBJECT, "Super-Extension2", parama=222)
    custom = CustomHeader(hname="MyCustomHeader", hvalue="MyCustomValue", param1="FortyTwo", X=0.1)

    hlist = HeaderList()
    hlist.add(na1)
    hlist.add(na2)
    hlist.add(na3)
    hlist.add(Cseq)
    hlist.add(subject1)
    hlist.add(custom)
    hlist.add(subject2)

    #print("vars:", vars(hlist))
    print("------------------")
    test = str(hlist)
    print(test)
