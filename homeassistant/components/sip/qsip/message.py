# TODO: Future Header Support:

from .msg_util import *
from .headers import HeaderEnum, HeaderList, CustomHeader, Header, NameAddress, CseqHeader


class msg():
    """Base class for SIP Request and Response"""

    def __init__(self, *, from_info, to_info, body=""):
        self.body = body[:]
        self.headers = {}
        self._from = from_info
        self._to = to_info

        populateMandatoryHeaders(self.headers)


    def setAddresses(self, *, fromInfo, toInfo, request_uri=None) -> None:
        """
        :param fromInfo:
        :param toInfo:
        :param request_uri:
        :return:
        """


class request(msg):

    def __init__(self, *, headers: HeaderList, body: str, request_uri: str):
        if request_uri is not None:
            self._request_uri = request_uri
        else
            self._request_uri = to_info["uri"]


class response():

    def __init__(self, response_code, response_text, headers, body):
