import socket
import hashlib
import random
import time
from enum import Enum

class PROTOCOL(Enum):
    TCP = 0
    UDP = 1
    SCTP = 2

class IP_VERSION(Enum):
    V6 = 0
    V4 = 1


def create_socket(proto : PROTOCOL, ip_version : IP_VERSION) -> socket:
    """Connect/authenticate to SIP Server."""
    # TODO: AF_INET6, udp

    if proto == PROTOCOL.UDP and ip_version == IP_VERSION.V4:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except socket.error as err:
            _LOGGER.exception("Socket creation failed with error %s" % (err))
    else:
        return None ### TQ-TODO: v6, tcp

    print("Socket successfully created: FileNo: ", s.fileno())

    if proto == PROTOCOL.TCP:
        try:
            # TQ-CHECK: Strange undefined symbol SO_REUSEPORT, for python-3.8 on win10?
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            print("SetSockOpt(SO_REUSEPORT)")
        except socket.error as err:
            _LOGGER.exception("setsockOpt(SO_REUSEPORT) error %s" % (err))

        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            print("SetSockOpt(SO_REUSEADDR)")
        except socket.error as err:
            _LOGGER.exception("setsockOpt(SO_REUSEADDR) error %s" % (err))

    return s


def bind_socket(my_socket: socket, *, bindAddress ="", bindPort = 0) -> bool:
    """"""
    try:    ### TODO: Acquire local-IP. Will be 172.x in docker...
        print(f"Trying to bind socket({my_socket.fileno()}) with: [{bindAddress}] and Port: [{bindPort}]")
        ### TQ-TODO: IpV6 will expect a 4-tuple.
        my_socket.bind((bindAddress, 0))
    except socket.error as err:
        print("Socket bind failed with error %s" % (err))
        return False
    print("Socket bound successfully: ", my_socket.getsockname())
    return True


def connect_socket(my_socket : socket, dst_addr : str, dst_port : int):
    """This is needed to get the local IP and Port"""

    print(f"Will (attempt to) connect with: socket({my_socket.fileno()}), towards {dst_addr}, {dst_port}")
    try:
        my_socket.connect((dst_addr, dst_port))
    except socket.error as err:
        print("Socket connect failed: ", my_socket, " ", err)
        return "", 0

    (localAddr, localPort) = my_socket.getsockname()
    return (localAddr, localPort)



class qsip():

    def __init__(self,
                 localIpInfo=None,
                 outgoingProxyInfo=None,
                 protocol = "UDP"):

        """Initialize the SIP service."""

        self._username = ""
        self._password = ""

        if  outgoingProxyInfo is None:
            self._outgoingProxyInfo = dict(addr="", port=0)
        else:
            # TODO  Validate Dict entry.
            # outgoingProxyInfo{"addr"} = IPv4/Host/IPv6 (eventually)
            # outgoingProxyInfo{"port"} = DNS NAPTR instead? 0 TODO: Should mean NAPTR?
            # TODO: PreCreate Route-header.
            self._outgoingProxyInfo = outgoingProxyInfo

        if localIpInfo is None:
            # TODO  Validate Dict entry.
            self._localIpInfo = dict(addr="", port=0)
        else:
            self._localIpInfo = localIpInfo
            print("LocalIPInfo set to: ", localIpInfo)

        self._protocol = PROTOCOL.UDP #For now.

        # Since we're binding and connecting the socket towards each specific dstAddr, we need to keep track of which is
        # which. Its currently based on key="addr", but with TCP support, we're gonna have to change that. TODO: TCP/UDP
        self._socketStorage = {}
        self._messageQueue = []


    def get_socket(self, dst_addr: str, dst_port : int) -> socket:
        if dst_addr not in self._socketStorage.keys():
            mysocket = create_socket(PROTOCOL.UDP, IP_VERSION.V4) ### TQ-TODO: Hardcoded

            if bind_socket(mysocket, bindAddress=self._localIpInfo["addr"], bindPort=self._localIpInfo["port"]):
                # We need to connect, to get local Ip:port
                local_address, local_port = connect_socket(mysocket, dst_addr, dst_port)
                if local_port > 0:
                    self._socketStorage[dst_addr] = (mysocket, local_address, local_port)
                    return mysocket, local_address, local_port
                else:
                    # Error connecting socket
                    bool #TODO: Errorhandling.
            else:
                # Error binding socket
                bool #TODO: Errorhandling.
            return None, "", 0
        else:
            return self._socketStorage[dst_addr]

    def closeSocket(self, dst_addr: str, dst_port : int):
        """Close on timeout? But we need to keep nat-mapping up?"""
        return True

    def sendRegister(self, dstAddress, dstPort, dstUri):
        """"""
        # TODO: Impl
        bool

    def registerUser(self, username: str, password: str):
        """Send REGISTER to proxy_address"""
        # TODO: Handle 401 Auth.
        # TODO: Check returned ;expires=,
        # Start Timer for Re-Registration with half that value.

        self._username = username
        self._password = password

        #qsip.sendRegister(self._username, self._password)

    def sendRequest(self, method: str, request_uri: str, body: str, headers=None) -> bool:
        """
        Send any SIP Request
        :param method:
        :param request_uri:
        :param body:
        :param headers:
        :return:
        """
        if not isinstance(headers, dict):
            return False;
        if not validateDefaultHeaders(headers):
            return False

        populateMandatoryHeaders(headers)



    def sendMessage(self, dst_addr: str, dst_port: int, request_uri: str, body: str) -> int:
        """Send a SIP message to a specific IP-destination, with a specific dst-uri?"""
        ### TODO: We'll most definitely need ;rport. ==> Currently hardcoded into via-header.

        current_socket, local_addr, local_port = self.get_socket(dst_addr, dst_port)

        if local_port == 0 or current_socket is None:
            print("Failed binding/connecting")
            return 0
        print(f"Source is: {local_addr}, Port: {local_port}, with socket: {current_socket.fileno()}")

        msg = str(requestTemplate)
        msg = msg.replace(templateMap["method"], "OPTIONS")
        msg = msg.replace(templateMap["requri"], request_uri)
        msg = msg.replace(templateMap["from"], "sip:taisto@trippelsteg.se")
        msg = msg.replace(templateMap["to"], request_uri)
        msg = msg.replace(templateMap["route"], "sip:proxy@10.9.24.1:5060")
        viaHost = local_addr + ":" + str(local_port)
        msg = msg.replace(templateMap["viahost"], viaHost)
        #msg = msg.replace(templateMap["viabranch"], generateViaBranch())
        msg = msg.replace(templateMap["contact"], "sip:taisto@10.9.24.44:5060")
        msg = msg.replace(templateMap["callid"], "dsadasdasda")
        msg = msg.replace(templateMap["cseqnr"], "5")
        msg = msg.replace("__CONTENT_LENGTH__", str(len(body)) )
        msg = msg + "\r"
        msg = msg + body
        result = current_socket.sendto(msg.encode(), (dst_addr, dst_port))

        if result != len(msg.encode()):
            current_socket.close()
            print("Failed Sending Entire message")
            # TODO: Remove from socket storage
        return result

def testFunc(MyDict : dict, **kwargs):
    params = MyDict
    for param in params.keys():
        print(f"Parameter key: {param} has value {params[param]}")
    params["Pelle"] = 42
    if len(kwargs.keys()) == 0:
        print("No EXTRA Named parameters", kwargs)

if __name__ == "__main__":
    sipSender = qsip({"addr": "", "port": 0})

    # digestResponse = calc_digest_response("bob","bee.net", "bob", "REGISTER", "sip:bee.net",
    #                                       "49e4ab81fb07c2228367573b093ba96efd292066",
    #                                       "00000001", "8d82cf2d1e7ff78b28570c311d2e99bd", "HejsanSvejsan")
    # print("Challenge Response: ", digestResponse)

#    result = sipSender.sendMessage("10.9.24.132", 5060, "sip:taisto@trippelsteg.se", "HejsanSvejsan1")
    time.sleep(1)

    myDict = {}
    myDict["kalle"] = 1
    myDict["Pelle"] = 2
    testFunc(myDict)
    print(myDict)
