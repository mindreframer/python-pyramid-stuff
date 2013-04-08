from __future__ import with_statement

import os
import sys

from zope.interface import implements
from repoze.sendmail.delivery import QueuedMailDelivery
from repoze.sendmail.interfaces import IMailDelivery

from karl.utils import get_settings

def boolean(s):
    s = s.lower()
    return s.startswith('y') or s.startswith('1') or s.startswith('t')

def mail_delivery_factory(os=os): # accepts 'os' for unit test purposes
    """Factory method for creating an instance of repoze.sendmail.IDelivery
    for use by this application.
    """
    settings = get_settings()

    # If settings utility not present, we are probably testing and should
    # suppress sending mail.  Can also be set explicitly in environment
    # variable
    suppress_mail = boolean(os.environ.get('SUPPRESS_MAIL', ''))

    if not settings or suppress_mail:
        return FakeMailDelivery()

    md = KarlMailDelivery(settings)
    if settings.get("mail_white_list", None):
        md = WhiteListMailDelivery(md)
    return md


class KarlMailDelivery(QueuedMailDelivery):
    """
    Uses queued mail delivery from repoze.sendmail, but provides the envelope
    from address from Karl configuration.
    """

    def __init__(self, settings):
        self.mfrom = settings.get('envelope_from_addr', None)
        self.bounce_from = settings.get(
            'postoffice.bounce_from_email', self.mfrom)
        queue_path = settings.get("mail_queue_path", None)
        if queue_path is None:
            # Default to var/mail_queue
            # we assume that the console script lives in the 'bin' dir of a
            # sandbox or buildout, and that the mail_queue directory lives in
            # the 'var' directory of the sandbox or buildout
            exe = sys.executable
            sandbox = os.path.dirname(os.path.dirname(os.path.abspath(exe)))
            queue_path = os.path.join(
                os.path.join(sandbox, "var"), "mail_queue"
            )
            queue_path = os.path.abspath(os.path.normpath(
                os.path.expanduser(queue_path)))

        QueuedMailDelivery.__init__(self, queue_path)

    def send(self, mto, msg):
        QueuedMailDelivery.send(self, self.mfrom, mto, msg)

    def bounce(self, mto, msg):
        QueuedMailDelivery.send(self, self.bounce_from, mto, msg)


class FakeMailDelivery:
    implements(IMailDelivery)

    def __init__(self, quiet=True):
        self.quiet = quiet

    def send(self, mto, msg):
        if not self.quiet: #pragma NO COVERAGE
            print 'To:', mto
            print 'Message:', msg

    bounce = send


class WhiteListMailDelivery(object):
    """Decorates an IMailDelivery with a recipient whitelist"""
    implements(IMailDelivery)

    def __init__(self, md):
        self.md = md
        settings = get_settings()
        white_list_fn = settings.get("mail_white_list", None)
        if white_list_fn:
            with open(white_list_fn) as f:
                self.white_list = set(
                    self._normalize(line) for line in f.readlines())
        else:
            self.white_list = None

    def _get_queuePath(self):
        return self.md.queuePath
    def _set_queuePath(self, value):
        self.md.queuePath = value
    queuePath = property(_get_queuePath, _set_queuePath)

    def send(self, toaddrs, message):
        self._send(toaddrs, message, self.md.send)

    def bounce(self, toaddrs, message):
        self._send(toaddrs, message, self.md.bounce)

    def _send(self, toaddrs, message, send):
        if self.white_list is not None:
            toaddrs = [addr for addr in toaddrs
                if self._normalize(addr) in self.white_list]
        if toaddrs:
            send(toaddrs, message)

    @staticmethod
    def _normalize(addr):
        if '<' in addr:
            addr = addr[addr.index('<') + 1:addr.rindex('>')]
        return unicode(addr.strip()).lower()

