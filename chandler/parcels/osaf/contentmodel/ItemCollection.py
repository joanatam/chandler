__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import osaf.contentmodel.ContentModel as ContentModel
import repository.query.Query as RepositoryQuery
from repository.item.ItemError import NoSuchIndexError
import traceback

class ItemCollection(ContentModel.ContentItem):
    myKindID = None
    myKindPath = "//parcels/osaf/contentmodel/ItemCollection"

    def onItemLoad(self, view):
        self._callbacks = {}
        self._updateCount = 0 # transient
        self._resultsLength = -1

    def subscribe (self, callbackItem=None, callbackMethodName=None):
        """
          Subscribed ItemCollections will automatically results up to date. Optionally,
        you can specify a method on an item to be called when the results change. There
        may be more than one subscriber.
        """
        if not self._isInitialized():
            assert self.itsView.isRefCounted(), "must be run repository with refcounting"
            self._setInitialized()
            try:
                path = '//Queries/' + self.__computeQueryName()
                self._query = self.findPath(path)
                if not self._query:
                    self._query = self.createRepositoryQuery()
                else:
                    self._callbacks = {} # shouldn't need to do this, but createRepository does it
            except NoSuchAttributeError:
                self._query = self.createRepositoryQuery()
            self._query.subscribe (self, "onItemCollectionChanged")
            self._query.stale = True
            self.resultsStale = True
            self.notifyOfChanges ("multiple changes")
        if callbackItem is not None:
            self._callbacks [callbackItem.itsUUID] = callbackMethodName

    def _isInitialized(self):

        return self.__dict__.get('_initialized', False)

    def _setInitialized(self, initialized=True):

        self.__dict__['_initialized'] = initialized

    def __computeQueryName(self):
        if self._name:
            return self._name+"Query"
        else:
            return str(self.itsUUID)+"Query"

    def createRepositoryQuery (self):
        self._callbacks = {} # transient
        # these two should be cached
        parent = self.findPath('//Queries')
        kind = self.findPath('//Schema/Core/Query')
        name = self.__computeQueryName()
        self._query = RepositoryQuery.Query (name, parent, kind, '') # transient
        self._updateCount = 0 # transient
        self.queryStringStale = True
        return self._query

    def unsubscribe (self, callbackItem=None):
        """
          If you don't specify a callbackItemUUID, all subscriptions will be removed.

          When an ItemCollections is unsubcribed, resultsStale may be inaccurate and
        the results will not be updated automatically. To update results on an unsubscribed
        ItemCollection, call updateResults.        
        """
        if callbackItem is None:
            self._callbacks = {}
        else:
            del self._callbacks [callbackItem.itsUUID]

        if len (self._callbacks) == 0:
            remainingSubscribers = self._query.unsubscribe (self)
            if remainingSubscribers == 0:
                del self._query
                del self._callbacks
                self._setInitialized(False)
                assert self.itsView.isRefCounted(), "respoitory must be opened with refcounted=True"
    
    def onItemCollectionChanged (self, action):
        self.resultsStale = True
        self.notifyOfChanges (action)

    def notifyOfChanges (self, action):
        if self._isInitialized() and self._updateCount == 0:
            for callbackUUID in self._callbacks.keys():
                item = self.find (callbackUUID)
                method = getattr (type(item), self._callbacks [callbackUUID])
                method (item, action)

    def add (self, item):
        """
          Add an item to the _inclusions
        """
        if item not in self._inclusions:
            self._inclusions.append (item)
            if item in self._exclusions:
                self._exclusions.remove (item)
            if item not in self._results:
                self._results.append (item)
            self.queryStringStale = True
            self.notifyOfChanges ("entered")

    def remove (self, item):
        """
          Remove an item from the _exclusions
        """
        if item not in self._exclusions:
            self._exclusions.append (item)
            if item in self._inclusions:
                self._inclusions.remove (item)
            if item in self._results:
                self._results.remove (item)
            self.queryStringStale = True
            self.notifyOfChanges ("exited")

    def addFilterKind (self, item):
        """
          Add an kind to the list of kinds to filter
        """
        kindPath = str (item.itsPath)
        if kindPath not in self._filterKinds:
            self._filterKinds.append (kindPath)
            self.queryStringStale = True
            self.notifyOfChanges ("exited")

    def removeFilterKind (self, item):
        """
          Remove an kind to the list of kinds to filter. If item is not None remove all filters
        """
        if item is not None:
            self._filterKinds.remove (str (item.itsPath))
        else:
            del self._filterKinds[:]
        self.queryStringStale = True
        self.notifyOfChanges ("entered")

    def beginUpdate (self):
        """
          When making lots of modifications to _inclusions, exclusion, rule or _filterKinds
        surround the changes with beginUpdate and endUpdate to avoid causing each change
        to send a separate event as in:

          itemCollection.beginUpdate()
          try:
              for item in list:
                  itemCollection.add (item)
          finally:
              itemCollection.endUpdate()

          Don't call beginUpdate unless the ItemCollection is subscribed.
        """
        self._updateCount += 1

    def endUpdate (self):
        """
          See endUpdate.
        """
        self._updateCount -= 1
        if self._updateCount == 0:
            self.notifyOfChanges ("multiple changes")

    def getRule (self):
        return self._rule

    def setRule (self, value):
        """
          When setting the rule, make sure we set resultsStale and queryStringStale
        """
        self.resultsStale = True
        self.queryStringStale = True
        self._rule = value

    rule = property (getRule, setRule)

    def getResults (self):
        """
          Override getting results to make sure it isn't stale
        """
        if self.resultsStale or self.queryStringStale:
            self.updateResults()
        return self._results

    results = property (getResults)

    def updateResults (self):
        """
         Refresh the cached query results by executing the repository query if necessary
        """
        try:
            query = self._query
        except AttributeError:
            path = '//Queries/'+self.__computeQueryName()
            self._query = self.findPath(path)
            if not self._query:
                self.createRepositoryQuery()
            query = self._query
            self.queryStringStale = True
            
        if self.queryStringStale:
            query.queryString, query.args = self.calculateQueryStringAndArgs()
            self.queryStringStale = False
            self.resultsStale = True
        if self.resultsStale or not self._isInitialized():
            current = None  # current is the "insertion point" for _results
            # make _results look like query:
            for item in query:
                if item in self._results:
                    self._results.placeItem(item, current)
                else:
                    self._results.insertItem(item, current)
                if current is None:
                    current = self._results.first()
                else:
                    current = self._results.next(current)

            # remove all remaining items in _results that weren't in query:
            if current is None:
                current = self._results.first()
            else:
                current = self._results.next(current)
            while current is not None:
                next = self._results.next(current)
                self._results.remove(current)
                current = next

            self.resultsStale = False

    def calculateQueryStringAndArgs (self):
        args = {}
        rule = self._rule
        if len (self._inclusions):
            if rule:
                rule = "union (" + rule + ", for i in $0 where True)"
            else:
                rule = "for i in $0 where True"
            args ["$0"] = (self.itsUUID, "_inclusions")
        if rule:
            if len (self._exclusions):
                rule = "difference (" + rule + ", for i in $1 where True)"
                args ["$1"] = (self.itsUUID, "_exclusions")
            if len (self._filterKinds) != 0:
                for kindPath in self._filterKinds:
                    rule = "intersect (" + rule + ", for i inevery '" + kindPath + "' where True)"
        return (rule, args)

    def shareSend (self):
        """
          Share this Item, or Send it (if it's an Email)
        """
        # message the mainView to do the bulk of the work, showing progress
        Globals.views[0].postEventByName ('ShareItem', {'item': self})

    def __len__ (self):
        try:
            if self.resultsStale or self._resultsLength < 0:
                self._resultsLength = len(self.results)
        except AttributeError:
            self._resultsLength = len(self.results)
        return self._resultsLength

    def __iter__ (self):
        for item in self.results:
            yield item

    def __contains__ (self, item):
        return item in self.results

    def __getitem__ (self, index):
        try:
            return self.results.getByIndex (self.indexName, index)
        except NoSuchIndexError:
            self.createIndex()
            return self._results.getByIndex (self.indexName, index)

    def __delitem__(self, index):
        self.remove (self.results [index])

    def createIndex (self):
        if self.indexName == "__adhoc__":
            self._results.addIndex (self.indexName, 'numeric')
        else:
            self._results.addIndex (self.indexName, 'attribute', attribute=self.indexName)

    def index (self, item):
        try:
            return self.results.getIndexPosition (self.indexName, item)
        except NoSuchIndexError:
            self.createIndex()
            return self._results.getIndexPosition (self.indexName, item)


