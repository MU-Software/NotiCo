import base64
import imaplib
import smtplib
import urllib.parse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import httpx
import pydantic

# import lxml.html

GOOGLE_ACCOUNTS_BASE_URL = "https://accounts.google.com"
GMAIL_DEFAULT_SCOPE = "https://mail.google.com/"
REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"


class GmailIMAP(pydantic.BaseModel):
    host: str = "imap.gmail.com"
    port: int = 993
    client_id: str
    auth_string: str  # TODO: Should rename this

    debuglevel: int = 4

    @property
    def connection(self) -> imaplib.IMAP4_SSL:
        imap_conn = imaplib.IMAP4_SSL(self.host)
        imap_conn.debug = self.debuglevel
        imap_conn.authenticate("XOAUTH2", lambda x: self.auth_string.encode("ascii"))
        return imap_conn

    @classmethod
    def test(cls, auth_string: str) -> None:
        conn = cls(client_id="test", auth_string=auth_string).connection
        conn.select("INBOX")


class GmailSMTP(pydantic.BaseModel):
    host: str = "smtp.gmail.com"
    port: int = 587
    client_id: str
    auth_string: str  # TODO: Should rename this

    debug: bool = False

    @pydantic.field_validator("auth_string", mode="after")
    @classmethod
    def validate_auth_string(cls, v: str) -> str:
        return base64.b64encode(v.encode("ascii")).decode("ascii")

    def get_connection(self) -> smtplib.SMTP:
        smtp_conn = smtplib.SMTP(self.host, self.port)
        smtp_conn.set_debuglevel(self.debug)
        smtp_conn.ehlo(self.client_id)
        smtp_conn.starttls()
        f"XOAUTH2 {self.auth_string}"
        smtp_conn.docmd("AUTH", f"XOAUTH2 {self.auth_string}")
        return smtp_conn

    @classmethod
    def test(cls, auth_string: str) -> None:
        with cls(client_id="test", auth_string=auth_string).get_connection():
            pass

    def sendmail(self, from_addr: str, to_addrs: list[str], msg: str) -> None:
        with self.get_connection() as conn:
            conn.sendmail(from_addr=from_addr, to_addrs=to_addrs, msg=msg)


def send_mail(
    client_id: str,
    client_secret: str,
    refresh_token: str,
    fromaddr: str,
    toaddr: str,
    subject: str,
    message: str,
    debug: bool = False,
) -> None:
    access_token = (
        httpx.post(
            url=f"{GOOGLE_ACCOUNTS_BASE_URL}/o/oauth2/token",
            content={
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        .raise_for_status()
        .json()["access_token"]
    )
    auth_string = f"user={fromaddr}\x01auth=Bearer {access_token}\x01\x01"

    msg = MIMEMultipart(_subtype="related")
    msg["Subject"] = subject
    msg["From"] = fromaddr
    msg["To"] = toaddr
    msg.preamble = "This is a multi-part message in MIME format."
    msg_alternative = MIMEMultipart("alternative")
    msg.attach(msg_alternative)
    part_text = MIMEText(
        # TODO: FIXME: use another method instead of lxml.html.fromstring
        # lxml.html.fromstring(message).text_content().encode("utf-8"), "plain", _charset="utf-8"
        ""
    )
    part_html = MIMEText(message, "html", _charset="utf-8")
    msg_alternative.attach(part_text)
    msg_alternative.attach(part_html)

    GmailSMTP(client_id=client_id, auth_string=auth_string, debug=debug).sendmail(fromaddr, [toaddr], msg.as_string())


if __name__ == "__main__":
    client_id = input("Enter your GOOGLE_CLIENT_ID: ")
    client_secret = input("Enter your GOOGLE_CLIENT_SECRET: ")

    params = {
        "scope": GMAIL_DEFAULT_SCOPE,
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
    }
    permission_url = f"{GOOGLE_ACCOUNTS_BASE_URL}/o/oauth2/auth?{urllib.parse.urlencode(params, safe='~-._')}"

    print(f"Navigate to the following URL to auth : {permission_url}")
    response = (
        httpx.post(
            url=f"{GOOGLE_ACCOUNTS_BASE_URL}/o/oauth2/token",
            content={
                "grant_type": "authorization_code",
                "code": input("Enter verification code: "),
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": REDIRECT_URI,
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        .raise_for_status()
        .json()
    )
    print(f"Google refresh token is : {response['refresh_token']}")
