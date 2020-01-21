


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

