""" Classes used for Contacts parcel kinds
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"
__parcel__ = "osaf.contentmodel.contacts"

from osaf.contentmodel import ContentModel
from application import schema
import repository.query.Query as Query
from repository.item.Query import KindQuery


class ContactName(ContentModel.ContentItem):

    myKindID = None
    myKindPath = "//parcels/osaf/contentmodel/contacts/ContactName"

    firstName = schema.One(schema.String, initialValue="")
    lastName  = schema.One(schema.String, initialValue="")
    contact = schema.One()  # Contact

    def __init__(self, name=None, parent=None, kind=None, view=None):
        super (ContactName, self).__init__(name, parent, kind, view)


class Contact(ContentModel.ContentItem):
    """An entry in an address book.

    Typically represents either a person or a company.

    * issue: We might want to keep track of lots of sharing information like
      'Permissions I've given them', 'Items of mine they've subscribed to',
      'Items of theirs I've subscribed to', etc.
    """
    myKindID = None
    myKindPath = "//parcels/osaf/contentmodel/contacts/Contact"

    schema.kindInfo(displayName="Contact", displayAttribute="emailAddress")
    
    itemsCreated = schema.Sequence(
        displayName="Items Created",
        doc = "List of content items created by this user.",
        inverse=ContentModel.ContentItem.creator,
    )

    contactName = schema.One(
        ContactName, inverse=ContactName.contact, initialValue=None
    )

    emailAddress = schema.One(schema.String, 
        displayName = "Email Address",
        initialValue = ""
    )

    itemsLastModified = schema.Sequence(
        ContentModel.ContentItem,
        displayName="Items Last Modified",
        doc="List of content items last modified by this user.",
        inverse=ContentModel.ContentItem.lastModifiedBy
    )

    requestedTasks = schema.Sequence(   # TaskMixin
        displayName="Requested Tasks",
        doc="List of tasks requested by this user.",
        otherName="requestor"
    )

    taskRequests= schema.Sequence(  # TaskMixin
        displayName="Task Requests",
        doc="List of tasks requested for this user.",
        otherName="requestee"
    )

    organizedEvents= schema.Sequence(   # CalendarEventMixin
        displayName="Organized Events",
        doc="List of events this user has organized.",
        otherName="organizer"
    )

    participatingEvents= schema.Sequence(   # CalendarEventMixin
        displayName="Participating Events",
        doc="List of events this user is a participant.",
        otherName="participants"
    )

    sharerOf= schema.Sequence(  # Share
        displayName="Sharer Of",
        doc="List of shares shared by this user.",
        otherName="sharer"
    )

    shareeOf= schema.Sequence(  # Share
        displayName="Sharee Of",
        doc="List of shares for which this user is a sharee.",
        otherName="sharees"
    )

    # <!-- redirections -->

    who   = schema.Role(redirectTo="contactName")
    about = schema.Role(redirectTo="displayName")
    date  = schema.Role(redirectTo="createdOn")


    def __init__(self, name=None, parent=None, kind=None, view=None):
        super (Contact, self).__init__(name, parent, kind, view)

        # If I didn't get assigned a creator, then I must be the "me" contact
        # and I want to be my own creator:
        if self.creator is None:
            self.creator = self

    def InitOutgoingAttributes (self):
        """ Init any attributes on ourself that are appropriate for
        a new outgoing item.
        """
        try:
            super(Contact, self).InitOutgoingAttributes ()
        except AttributeError:
            pass

        self.contactName = ContactName()
        self.contactName.firstName = ''
        self.contactName.lastName = ''

    def getCurrentMeContact(cls, view):
        """ Lookup the current "me" Contact """

        # cls.meContactID caches the Contact representing the user.  One will
        # be created if it doesn't yet exist.

        if cls.meContactID is not None:
            me = view.findUUID(cls.meContactID)
            if me is not None:
                return me
            # Our cached UUID is invalid
            cls.meContactID is None

        parent = ContentModel.ContentModel.getContentItemParent(view)
        me = parent.getItemChild("me")
        if me is None:
            me = Contact(name="me", parent=parent)
            me.displayName = "Me"
            me.contactName = ContactName(parent=me)
            me.contactName.firstName = "Chandler"
            me.contactName.lastName = "User"

        cls.meContactID = me.itsUUID

        return me

    getCurrentMeContact = classmethod(getCurrentMeContact)

    # Cache "me" for fast lookup; used by getCurrentMeContact()
    meContactID = None


    def getContactForEmailAddress(cls, view, address):
        """ Given an email address string, find (or create) a matching contact.

        @param view: The repository view object
        @type view: L{repository.persistence.RepositoryView}
        @param address: An email address to use for looking up a contact
        @type address: string
        @return: A Contact
        """

        """ @@@MOR, convert this section to use Query; I tried briefly but
        wasn't successful, and it's just using KindQuery right now:

        query = Query.Query(view, parent=view.findPath("//userdata"), queryString="") # @@@MOR Move this to a singleton

        queryString = "for i in '//parcels/osaf/contentmodel/contacts/Contact' where i.emailAddress == $0"
        query.args = { 0 : address }
        query.execute()
        for item in query:
        """

        for item in KindQuery().run([view.findPath("//parcels/osaf/contentmodel/contacts/Contact")]):
            if item.emailAddress == address:
                return item # Just return the first match

        # Need to create a new Contact
        contact = Contact(view=view)
        contact.emailAddress = address
        contact.contactName = None
        return contact

    getContactForEmailAddress = classmethod(getContactForEmailAddress)

    def __str__(self):
        """ User readable string version of this address. """

        if self.isStale():
            return super(Contact, self).__str__()
            # Stale items shouldn't go through the code below

        value = self.getItemDisplayName()

        return value


