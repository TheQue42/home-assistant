


def generateCallId():
    return "SuperRandomCallId" + str(random.randint(0, 2**32-1))

def generateViaBranch(addMagicCookie=False):
    return True
pzatpo

def populateMandatoryHeaders(headers):
    headers["Via"] = "Via: SIP/2.0/UDP 10.9.24.44:51915;rport;branch=z9hG4bK__VIA_BRANCH__"
    headers["Max-Forwards"] = "Max-Forwards: 70"
    headers["CSeq"] = "CSeq: __METHOD__" + str(random.randint(0, 2**32-1))
    headers["Call-Id"] = "Call-Id: " + "SuperRandomCallId" + str(random.randint(0, 2**32-1))
    # To, From,
    # Via, CSeq, Call-Id, Max-Forwards

templateMap = {
        "method": "__METHOD__",
        "requri": "__REQUEST_URI__",
        "viahost": "__VIA_HOST__",
        "viabranch": "__VIA_BRANCH__",
        "route": "__ROUTE_URI__",
        "contact": "__CONTACT_URI__",
        "cseqnr": "__CSEQ_NUMBER__",
        "callid": "__CALL_ID__",
        "to": "__TO_HEADER__",
        "from": "__FROM_HEADER__",
        "require": "__REQUIRE__"  ##TODO
    }

requestTemplate = '''__METHOD__ __REQUEST_URI__ SIP/2.0\r
Via: SIP/2.0/UDP __VIA_HOST__;rport;branch=z9hG4bK__VIA_BRANCH__\r
Route: <__ROUTE_URI__>;lr\r
Max-Forwards: 70\r
From: __FROM_HEADER__\r
To: __TO_HEADER__\r
Call-ID: __CALL_ID__\r
CSeq: __CSEQ_NUMBER__ __METHOD__\r
User-Agent: Qsip/0.0.0.0.0.1\r
Contact: __CONTACT_URI__\r
Expires: 0\r
Content-Type: text/plain\r
Content-Length:  __CONTENT_LENGTH__\r
'''

def calc_digest_response(self,
                         username: str,
                         realm: str,
                         password: str,
                         method: str,
                         uri: str,
                         nonce: str,
                         nonce_counter: str,
                         client_nonce: str) -> str:
    """
    Digest Authentication
    """
    HA1 = hashlib.md5()
    pre_HA1 = ":".join((username, realm, password))
    HA1.update(pre_HA1.encode())
    pre_HA2 = ":".join((method, uri))
    HA2 = hashlib.md5()
    HA2.update(pre_HA2.encode())
    nc = nonce_counter  ### TODO: Support nonce-reuse?
    list = (HA1.hexdigest(), nonce, nc, client_nonce, "auth", HA2.hexdigest())
    print("List is: ", list)
    preRsp = ":".join(list)
    response = hashlib.md5()
    response.update(preRsp.encode())
    return response.hexdigest()

