# TODO: Future Header Support:

from .msg_util import *

__VIA_MAGIC_COOKE = "z9hG4Bk"
class msg():
    """Base class for SIP Request and Response"""

    def __init__(self, *, from_info, to_info, request_uri = None, body=""):
        self.body = body[:]
        self.headers = {}
        self._from = from_info
        self._to = to_info
        if request_uri is not None:
            self._request_uri = request_uri
        else
            self._request_uri = to_info["uri"]

        populateMandatoryHeaders(self.headers)


    def setAddresses(self, *, fromInfo, toInfo, request_uri=None) -> None:
        """
        :param fromInfo:
        :param toInfo:
        :param request_uri:
        :return:
        """


class request(msg):

    def __init__(self, req_uri: str, headers, body):


class response():

    def __init__(self, response_code, response_text, headers, body):
