__all__ = ['email_server', 'email_server_dummy']

import cgi
from smtplib import SMTP
from email.mime.text import MIMEText
import email.charset
email.charset.add_charset('utf-8', email.charset.QP, email.charset.QP)

#steal from numpy
def _is_string_like(obj):
    """
    Check whether obj behaves like a string.
    """
    try:
        obj + ''
    except (TypeError, ValueError):
        return False
    return True

class email_server():
    def __init__(self):
        self._server = SMTP('localhost')

    def send(self, From, To, subject, message):
        mymail = MIMEText(message, 'html', 'utf-8')
        mymail['Subject'] = subject
        mymail['From'] = From
        if _is_string_like(To):
            To = [To]
        mymail['To'] = ', '.join(To)
        self._server.sendmail(From, To, mymail.as_string())

    def close(self):
        self._server.quit()

class email_server_dummy:
    def __init__(self):
        pass

    def close(self):
        pass

    def send(self, From, To, subject, message):
        if _is_string_like(To):
            To = [To]
        print '<h2>', cgi.escape(', '.join(To)), '</h2>'
        print message.encode('ascii', 'xmlcharrefreplace')
        print '<br/><hr/>'

