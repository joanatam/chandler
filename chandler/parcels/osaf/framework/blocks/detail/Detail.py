__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application
import application.Globals as Globals
import osaf.framework.blocks.Block as Block
import osaf.framework.blocks.DynamicContainerBlocks as DynamicContainerBlocks
import osaf.framework.blocks.ControlBlocks as ControlBlocks
import repository.persistence.XMLRepositoryView as XMLRepositoryView
import osaf.contentmodel.mail.Mail as Mail
import osaf.contentmodel.ContentModel as ContentModel
import osaf.contentmodel.tasks.Task as Task
import osaf.contentmodel.calendar.Calendar as Calendar
import osaf.contentmodel.Notes as Notes
import osaf.contentmodel.contacts.Contacts as Contacts
import wx

"""
Detail.py
Classes for the ContentItem Detail View
"""

class DetailParcel (application.Parcel.Parcel):
    pass

class DetailRoot (ControlBlocks.SelectionContainer):
    """
      Root of the Detail View.
    """
    def onSelectionChangedEvent (self, notification):
        """
          We have an event boundary inside us, which keeps all
        the events sent between blocks of the Detail View to
        ourselves.
          When we get a SelectionChanged event, we jump across
        the event boundary and call synchronizeItemDetail on each
        block to give it a chance to synchronize on the details of
        the Item.  
          Notify container blocks before their children.
        """
        super(DetailRoot, self).onSelectionChangedEvent(notification)
        item= self.selectedItem()
        assert item is notification.data['item'], "can't track selection in DetailRoot.onSelectionChangedEvent"
        self.synchronizeWidget()

    def synchronizeDetailView(self, item):
        """
          We have an event boundary inside us, which keeps all
        the events sent between blocks of the Detail View to
        ourselves.
          When we get a SelectionChanged event, we jump across
        the event boundary and call synchronizeItemDetail on each
        block to give it a chance to synchronize on the details of
        the Item.  
          Notify container blocks before their children.
          
          DLDTBD - find a better way to broadcast inside my boundary.
        """
        def reNotifyInside(block, item):
            notifyParent = False
            try:
                for child in block.childrenBlocks:
                    notify = reNotifyInside (child, item)
                    notifyParent = notifyParent or notify
            except AttributeError:
                pass
            try:
                notify = block.synchronizeItemDetail(item)
                notifyParent = notifyParent or notify
            except AttributeError:
                if notifyParent:
                    block.synchronizeWidget()
            return notifyParent
        children = self.childrenBlocks
        for child in children:
            child.isShown = item is not None
            reNotifyInside(child, item)
    
    def synchronizeWidget (self):
        item= self.selectedItem()
        self.synchronizeDetailView(item)
        super(DetailRoot, self).synchronizeWidget ()
        
class DetailSynchronizer(object):
    """
      Mixin class that handles synchronizeWidget and
    the SelectionChanged event by calling synchronizeItemDetail.
    Most client classes will only have to implement
    synchronizeItemDetail.
    """
    def selectedItem (self):
        # delegate to our parent until we get outside our event boundary
        return self.parentBlock.selectedItem()

    def relayoutParents (self):
        # relayout the parent block
        block = self
        while (not block.eventBoundary and block.parentBlock):
            block = block.parentBlock
            block.synchronizeWidget()

    def synchronizeItemDetail (self, item):
        # if there is an item, we should show the From and To Area
        shouldShow = item is not None
        return self.show(shouldShow)
        
    def show(self, shouldShow):
        # if the show status has changed, tell our widget, and our parent
        if shouldShow != self.isShown:
            try:
                widget = self.widget
            except AttributeError:
                return False
            # we have a widget
            if shouldShow:
                widget.Show(True)
                self.isShown = True
            else:
                widget.Show(False)
                self.isShown = False
            return True
        return False

class StaticTextLabel (DetailSynchronizer, ControlBlocks.StaticText):
    def staticTextLabelValue (self, item):
        """ Override to provide the value of the static text label """
        raise NotImplementedError, "%s.staticTextLabelValue()" % (type(self))

    def synchronizeLabel (self, value):
        label = self.widget.GetLabel ()
        relayout = label != value
        if relayout:
            self.widget.SetLabel (value)
        return relayout

    def synchronizeItemDetail (self, item):
        return self.synchronizeLabel(self.staticTextLabelValue(item))

class DateTimeBlock (StaticTextLabel):
    """
    Date and Time associated with the Content Item
    Currently this is static text, but soon it will need to be editable
    """
    def staticTextLabelValue (self, item):
        """
          return the item's date.
        """
        theDate = item.date # get the redirected date attribute
        theDate = str(theDate)
        return theDate

class KindLabel (StaticTextLabel):
    """Shows the Kind of the Item as static text"""
    def staticTextLabelValue (self, item):
        """
          Display the item's Kind in the wxWidget.
        """
        return item.itsKind.displayName
        
class Headline (StaticTextLabel):
    """Headline, or Title field of the Content Item, as static text"""
    def staticTextLabelValue (self, item):
        return item.about
        
class StaticTextAttribute(StaticTextLabel):
    """
      Static Text that displays the name of the selected item's Attribute
    """
    def staticTextLabelValue (self, item):
        redirectAttr = item.getAttributeAspect(self.whichAttribute(), 'redirectTo')
        if redirectAttr is None:
            redirectAttr = '  '
        else:
            redirectAttr = ' ' + redirectAttr + ': '
        return redirectAttr

    def whichAttribute(self):
        # define the attribute to be used
        return self.parentBlock.selectedItemsAttribute

class LabeledTextAttributeBlock(ControlBlocks.ContentItemDetail):
    def synchronizeItemDetail(self, item):
        whichAttr = self.selectedItemsAttribute
        try:
            attr = item.getAttributeValue(whichAttr)
            self.isShown = attr is not None
        except AttributeError:
            self.isShown = item.hasAttributeAspect(whichAttr, 'redirectTo')
        self.synchronizeWidget()

class MarkupBar (DetailSynchronizer, DynamicContainerBlocks.Toolbar):
    """   
      Markup Toolbar, for quick control over Items.
    Doesn't need to synchronizeItemDetail, because
    the individual ToolbarItems synchronizeItemDetail.
    """
    def onToolPressStub (self, notification):
        tool = notification.data['sender']
        if tool.itsName == 'SharingButton':
            #self.parentBlock.Notify("EnableSharing")
            pass
    
    def onToolPressStubUpdateUI (self, notification):
        notification.data ['Enable'] = False

    def selectedItem (self):
        # return the ContentItem being viewed
        return self.parentBlock.selectedItem()

    def onButtonPressed (self, notification):
        # Rekind the item by adding or removing the associated Mixin Kind
        tool = notification.data['sender']
        # DLDTBD - use self instead of bar here, once block copy problem is fixed.
        bar = tool.dynamicParent
        item = bar.selectedItem()
        if item is not None:
            mixinKind = tool.stampMixinKind()
            if bar.widget.GetToolState(tool.toolID):
                operation = 'add'
            else:
                operation = 'remove'
            item.StampKind(operation, mixinKind)
            # notify the world that the item has a new kind.
            block = bar
            while block.eventBoundary == False:
                block = block.parentBlock
            block.parentBlock.synchronizeWidget()

    def onButtonPressedUpdateUI (self, notification):
        item = self.selectedItem()
        # DLDTBD - fix the line below to False when the block copy problem is fixed.
        enable = True
        if item is not None:
            enable = item.itsKind.isKindOf(ContentModel.getNoteKind())            
        notification.data ['Enable'] = enable

class DetailStampButton (DetailSynchronizer, DynamicContainerBlocks.ToolbarItem):
    """
      Common base class for the stamping buttons in the Markup Bar
    """
    def stampMixinClass(self):
        # return the class of this stamp's Mixin Kind (bag of kind-specific attributes)
        raise NotImplementedError, "%s.stampMixinClass()" % (type(self))
    
    def stampMixinKind(self):
        # return the Mixin Kind of this stamp
        raise NotImplementedError, "%s.stampMixinKind()" % (type(self))
    
    def synchronizeItemDetail (self, item):
        # toggle this button to reflect the kind of the selected item
        shouldToggleBasedOnClass = isinstance(item, self.stampMixinClass())
        shouldToggleBasedOnKind = item.itsKind.isKindOf(self.stampMixinKind())
        assert shouldToggleBasedOnClass == shouldToggleBasedOnKind, \
               "Class/Kind mismatch for class %s, kind %s" % (item.__class__, item.itsKind)
        self.dynamicParent.widget.ToggleTool(self.toolID, shouldToggleBasedOnKind)
        return False

class SharingButton (DetailStampButton):
    """
      Sharing button in the Markup Bar
    """
    def stampMixinClass(self):
        return Mail.MailMessageMixin
    
    def stampMixinKind(self):
        return Mail.MailParcel.getMailMessageMixinKind()
    
class CalendarStamp (DetailStampButton):
    """
      Calendar button in the Markup Bar
    """
    def stampMixinClass(self):
        return Calendar.CalendarEventMixin

    def stampMixinKind(self):
        return Calendar.CalendarParcel.getCalendarEventMixinKind()

class TaskStamp (DetailStampButton):
    """
      Task button in the Markup Bar
    """
    def stampMixinClass(self):
        return Task.TaskMixin

    def stampMixinKind(self):
        return Task.TaskParcel.getTaskMixinKind()

class EditTextAttribute (DetailSynchronizer, ControlBlocks.EditText):
    """
    EditText field connected to some attribute of a ContentItem
    Override LoadAttributeIntoWidget, SaveAttributeFromWidget in subclasses
    """
    def instantiateWidget (self):
        widget = super (EditTextAttribute, self).instantiateWidget()
        # We need to save off the changed widget's data into the block periodically
        # Currently looks like OnLoseFocus is not getting called every time we lose focus,
        #   only when focus moves to another EditText block.
        widget.Bind(wx.EVT_KEY_UP, self.onKeyUp)
        widget.Bind(wx.EVT_KILL_FOCUS, self.onLoseFocus)
        return widget

    def onKeyUp (self, event):
        self.saveTextValue()

    def saveTextValue (self):
        # save the user's edits into item's attibute
        item = self.selectedItem()
        widget = self.widget
        if item and widget:
            self.saveAttributeFromWidget(item, widget)
        
    def loadTextValue (self, item):
        # load the edit text from our attribute into the field
        if not item:
            item = self.selectedItem()
        if item:
            widget = self.widget
            self.loadAttributeIntoWidget(item, widget)
        
    def onLoseFocus (self, notification):
        # called when we lose focus, to save away the text
        self.saveTextValue()
        
    def OnDataChanged (self):
        # Notification that an edit operation has taken place
        self.saveTextValue()

    def synchronizeItemDetail (self, item):
        self.loadTextValue(item)
        return super(EditTextAttribute, self).synchronizeItemDetail(item)
            
    def saveAttributeFromWidget (self, item, widget):  
       # subclasses need to override this method
       raise NotImplementedError, "%s.SaveAttributeFromWidget()" % (type(self))

    def loadAttributeIntoWidget (self, item, widget):  
       # subclasses need to override this method
       raise NotImplementedError, "%s.LoadAttributeIntoWidget()" % (type(self))

class NoteBody (EditTextAttribute):
    """
    Body attribute of a ContentItem, e.g. a Note
    """
    def saveAttributeFromWidget (self, item, widget):  
        textType = item.getAttributeAspect('body', 'type')
        widgetText = widget.GetValue()
        if widgetText:
            item.body = textType.makeValue(widgetText)
        
    def loadAttributeIntoWidget (self, item, widget):  
        if item.hasAttributeValue("body"):
            # get the character string out of the Text LOB
            noteBody = item.body
            if isinstance(noteBody, XMLRepositoryView.XMLText):
                # Read the unicode stream from the XML
                noteBody = noteBody.getInputStream().read()
            widget.SetValue(noteBody)
        else:
            widget.Clear()

class ToEditField (EditTextAttribute):
    """
    Body attribute of a ContentItem, e.g. a Note
    """
    def saveAttributeFromWidget(self, item, widget):  
        toFieldString = widget.GetValue()
        # DLDTBD - need to parse the string and lookup the contacts
        #  because it's really the contacts that are stored in the "who" attribute!
       
    def loadAttributeIntoWidget (self, item, widget):
        try:
            whoContacts = item.who # get redirected who list
        except AttributeError:
            widget.SetValue('')
            return
        try:
            numContacts = len(whoContacts)
        except TypeError:
            numContacts = 0            
        if numContacts > 0:
            whoNames = []
            for whom in whoContacts.values():
                whoNames.append(whom.getItemDisplayName())
            whoString = ', '.join(whoNames)
        else:
            whoString = ''
            if isinstance(whoContacts, Contacts.ContactName):
                whoString = whoContacts.firstName + ' ' + whoContacts.lastName
        widget.SetValue(whoString)

class FromEditField (EditTextAttribute):
    """Edit field containing the sender's contact"""
    def saveAttributeFromWidget(self, item, widget):  
        pass       
    def loadAttributeIntoWidget(self, item, widget):
        pass

