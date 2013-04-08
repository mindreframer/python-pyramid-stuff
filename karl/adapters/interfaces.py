from zope.interface import Attribute
from zope.interface import Interface

class IMailinDispatcher(Interface):
    """ Adapter for doing generic mail-in processing.
    """
    default_tool = Attribute(u"""Name of the default tool for mail-in content.

                   Messages mailed to the community address go to this tool.""")

    text_scrubber = Attribute(u"""Name of the utility used to scrub text.

                    If set, used to look up an IMailinTextScrubber by name.""")

    def getAddrList(message, name):
        """ Return a list of addresses from headers of 'message' for 'name'.

        o Return an empty list if 'message' has no matching headers.
        """

    def isCommunity(name):
        """ Does the site hav a community matching 'name'?
        """

    def isReport(name):
        """ Does the site have a peopledir report matching 'name'?
        """

    def getCommunityId(email):
        """ Return the name of the community whose email matches 'email'.

        o Return None if no match is found.
        """

    def getAuthor(email):
        """ Return the URL name of the profile matching 'email'.

        o Return None if no match is found.
        """

    def crackHeaders(message):
        """Return a mapping specifying where the message should be posted.

        If the message should not be posted, the mapping will contain
        an 'error' key describing why.

        If there is no error, the mapping will contain at least the
        following keys:

          - 'community':  what community contains the target for the message?

          - 'tool':  what tool within the community contains the target?

          - 'in_reply_to':  what content item is the target?  If None, then
            the tool is the target.

          - 'author':  login ID of the author.

          - 'subject':  the message's subject line.

        Even if 'error' is set, the mapping may contain enough of those
        keys for a moderator to override and post the message anyway.
        """

    def crackPayload(message):
        """ Return (text, attachments), extracted from the message payload.

        o 'text' is the text of the message, extracted from the first
          'text/plain' part of the payload without a filename.

        o 'attachments':  a sequence of file attachment info, where
           each item is a tuple, (filename, mimetype, data) corresponding
           to message parts which have filenames.

           - 'mimetype' defaults to 'application/octet-stream', if the
             corresponding part contains no 'Content-Type' header.

           - 'data' will be decoded to bytes using the part's transfer
             encoding.  If the attachment is of a 'text/*' mimetype, data
             will be further decoded to unicode, using the part's charset.
        """

class IMailinHandler(Interface):
    """ Adapter for processing mail "to" a model object.
    """
    def handle(message, info, text, attachments):
        """ Do the Right Thing (TM).

        o 'message' is a repoze.postoffice.message.Message instance.

        o 'info' is a mapping extracted from the message by
          IMailinDispatcher.crackHeaders.

        o 'text' and 'adapters' are the values extracted from the message
          by IMailinDispatcher.crackPayload.
        """
