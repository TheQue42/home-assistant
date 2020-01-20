"""SIP (Session Initial Protocol) notification service."""
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import email.utils
import logging
import os
import qsip
import voluptuous as vol

from homeassistant.const import (
    CONF_PASSWORD,
    CONF_RECIPIENT,
    CONF_TIMEOUT,
    CONF_USERNAME,
)
import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util

from homeassistant.components.notify import (
    ATTR_DATA,
    ATTR_TITLE,
    ATTR_TITLE_DEFAULT,
    PLATFORM_SCHEMA,
    BaseNotificationService,
)

_LOGGER = logging.getLogger(__name__)

ATTR_IMAGES = "images"  # optional embedded image file attachments
ATTR_HTML = "html"

CONF_OUTGOING_PROXY = "outgoing_proxy"
CONF_OUTGOING_PROXY_PORT = "outgoing_proxy_port"
CONF_FROM = "from_address"
CONF_FROM_DISPLAYNAME = "from_displayname"
CONF_REGISTRAR_ADDRESS = "registrar_address"
CONF_REGISTRAR_PORT = "registrar_port"
CONF_SIP_T1_TIMER = "sip_t1_timer"
CONF_ENCRYPTION = "encryption"
CONF_DEBUG = "debug"

DEFAULT_PROXY = ""                                              # We dont need one for SIP.
DEFAULT_PROXY_PORT = 0                                          # 0 implies we wont use one.
DEFAULT_PROTOCOL = "udp"                                        # Tcp Not supported Yet
DEFAULT_DEBUG = False
DEFAULT_ENCRYPTION = "none"
DEFAULT_REGISTRAR_ADDRESS=""                                    # Use the "proxy_address" above, for REGISTER
DEFAULT_REGISTRAR_PORT = "0"                                    # 0 implies we don't REGISTER
DEFAULT_T1_TIMER = 100                                          # Millisec
DEFAULT_TIMEOUT = 64 * DEFAULT_T1_TIMER                         # Will be used as "T1 x 64"
ENCRYPTION_OPTIONS = ["tls", "starttls", "none"]

# pylint: disable=no-value-for-parameter
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        # voluptuous  doesnt support sip-uri's, so we'll have to use email format.
        vol.Required(CONF_RECIPIENT): vol.All(cv.ensure_list, [vol.Email()]),
        vol.Required(CONF_FROM): vol.Email(),
        vol.Optional(CONF_FROM_DISPLAYNAME): cv.string,
        vol.Optional(CONF_OUTGOING_PROXY, default=DEFAULT_PROXY): cv.string,
        vol.Optional(CONF_OUTGOING_PROXY_PORT, default=DEFAULT_PROXY_PORT): cv.positive_int,
        # vol.Optional(CONF_PROTOCOL, default=DEFAULT_PROTOCOL): cv.string,
        vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
        vol.Optional(CONF_ENCRYPTION, default=DEFAULT_ENCRYPTION): vol.In(ENCRYPTION_OPTIONS),
        vol.Optional(CONF_USERNAME): cv.string,
        vol.Optional(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_REGISTRAR_ADDRESS, default=DEFAULT_REGISTRAR_ADDRESS): cv.string,
        vol.Optional(CONF_REGISTRAR_PORT, default=DEFAULT_REGISTRAR_PORT): cv.positive_int,
        vol.Optional(CONF_SIP_T1_TIMER, default=DEFAULT_T1_TIMER): cv.positive_int,
        vol.Optional(CONF_DEBUG, default=DEFAULT_DEBUG): cv.boolean,
    }
)


def get_service(hass, config, discovery_info=None):
    """Get the SIP notification service."""
    sip_service = SipNotificationService(
        config.get(CONF_OUTGOING_PROXY),
        config.get(CONF_OUTGOING_PROXY_PORT),
        DEFAULT_PROTOCOL,                       ### TODO: Hard-coded for now
        config.get(CONF_TIMEOUT),
        config.get(CONF_FROM),
        config.get(CONF_FROM_DISPLAYNAME),
        config.get(CONF_ENCRYPTION),
        config.get(CONF_USERNAME),
        config.get(CONF_PASSWORD),
        config.get(CONF_RECIPIENT),
        config.get(CONF_REGISTRAR_ADDRESS),
        config.get(CONF_REGISTRAR_PORT),
        config.get(CONF_SIP_T1_TIMER),
        config.get(CONF_DEBUG),
    )

    # With a UDP socket, how to we know its valid?
    # Send OPTIONS, but that might not get Auth-ed, where as the MESSAGE will?
    if sip_service.connection_is_valid():
        return sip_service

    return None


class SipNotificationService(BaseNotificationService):
    """Implement the notification service for SIP messages."""

    def __init__(self,
                 proxy_address,  # Outgoing Proxy Address: IP or TODO: FQDN
                 proxy_port,  # Outgoing Proxy Port
                 protocol : str,
                 timeout,
                 from_address,
                 from_displayname,
                 encryption,
                 username,
                 password,
                 recipients,  # Multiple recipients?
                 registrar_address,
                 registrar_port,
                 timer_t1,
                 debug):

        """Initialize the SIP service."""
        self._proxy_address = proxy_address
        self._proxy_port = proxy_port

        if protocol.lower() == "udp":             # Hardcoded to UDP so far.
            self._proto = PROTOCOL.UDP
        else:
            self._proto = PROTOCOL.TCP       # SCP in the year of 2030

        self._timeout = timeout
        self._from_address = from_address
        self._encryption = encryption
        self._username = username
        self._password = password
        self._recipients = recipients
        self._from_displayName = from_displayname
        if self._registrar_port > 0:
            self._register_timer = 3600
            self._registrar_address = registrar_address
            self._registrar_port = registrar_port
        else:
            self._registrar_address = ""
            self._registrar_port = 0
            self._register_timer = 0
        self._timer_t1 = timer_t1
        self.debug = debug
        self.tries = 2
        self._sipSender = qsip()

    def connection_is_valid(self):
        """TODO"""
        # If registration is required, check that registration works.
        # If registration is NOT required, and we're using UDP, how do we validate?
        # ==> OPTIONS?
        if self._registrar_port > 0:
            qsip.registerUser(self._from_address, self._password)
        else if self._proxy_port > 0:
            qsip.sendOptions(self._from_address, self._proxy_address)
        else:
            return True

    def send_message(self, message="", **kwargs):
        """
        Build and send a message to a user.

        Will send plain text normally, or will build a multipart HTML message
        with inline image attachments if images config is defined, or will
        build a multipart HTML if html config is defined.
        NOTE: Quite a few SIP clients dont support HTML multipart.
        """
        subject = kwargs.get(ATTR_TITLE, ATTR_TITLE_DEFAULT)
        data = kwargs.get(ATTR_DATA)

        if data:
            if ATTR_HTML in data:
                msg = _build_html_msg(
                    message, data[ATTR_HTML], images=data.get(ATTR_IMAGES, [])
                )
            else:
                msg = _build_multipart_msg(message, images=data.get(ATTR_IMAGES, []))
        else:
            msg = _build_text_msg(message)

        ##TODO: Modify this into SIP from RFC822
        msg["Subject"] = subject
        msg["To"] = ",".join(self.recipients)
        if self._sender_name:
            msg["From"] = f"{self._from_displayName } <{self._from_address}>"
        else:
            msg["From"] = self._sender
        msg["User-Agent"] = "HomeAssistant QSip Module"
        msg["Date"] = email.utils.format_datetime(dt_util.now())
        ###TQ-TODO: Rest of SIP Message
        return True



def _build_text_msg(message):
    """Build plaintext email."""
    _LOGGER.debug("Building plain text email")
    return MIMEText(message)


def _build_multipart_msg(message, images):
    """Build Multipart message with in-line images."""
    _LOGGER.debug("Building multipart email with embedded attachment(s)")
    msg = MIMEMultipart("related")
    msg_alt = MIMEMultipart("alternative")
    msg.attach(msg_alt)
    body_txt = MIMEText(message)
    msg_alt.attach(body_txt)
    body_text = [f"<p>{message}</p><br>"]

    for atch_num, atch_name in enumerate(images):
        cid = f"image{atch_num}"
        body_text.append(f'<img src="cid:{cid}"><br>')
        try:
            with open(atch_name, "rb") as attachment_file:
                file_bytes = attachment_file.read()
                try:
                    attachment = MIMEImage(file_bytes)
                    msg.attach(attachment)
                    attachment.add_header("Content-ID", f"<{cid}>")
                except TypeError:
                    _LOGGER.warning(
                        "Attachment %s has an unknown MIME type. "
                        "Falling back to file",
                        atch_name,
                    )
                    attachment = MIMEApplication(file_bytes, Name=atch_name)
                    attachment["Content-Disposition"] = (
                        "attachment; " 'filename="%s"' % atch_name
                    )
                    msg.attach(attachment)
        except FileNotFoundError:
            _LOGGER.warning("Attachment %s not found. Skipping", atch_name)

    body_html = MIMEText("".join(body_text), "html")
    msg_alt.attach(body_html)
    return msg


def _build_html_msg(text, html, images):
    """Build Multipart message with in-line images and rich HTML (UTF-8)."""
    _LOGGER.debug("Building HTML rich email")
    msg = MIMEMultipart("related")
    alternative = MIMEMultipart("alternative")
    alternative.attach(MIMEText(text, _charset="utf-8"))
    alternative.attach(MIMEText(html, ATTR_HTML, _charset="utf-8"))
    msg.attach(alternative)

    for atch_num, atch_name in enumerate(images):
        name = os.path.basename(atch_name)
        try:
            with open(atch_name, "rb") as attachment_file:
                attachment = MIMEImage(attachment_file.read(), filename=name)
            msg.attach(attachment)
            attachment.add_header("Content-ID", f"<{name}>")
        except FileNotFoundError:
            _LOGGER.warning(
                "Attachment %s [#%s] not found. Skipping", atch_name, atch_num
            )
    return msg
