"""
Item tests for Parcel Loader
"""
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import ParcelLoaderTestCase, os, sys, unittest

from repository.parcel.Util import PrintItem
from repository.parcel.LoadParcels import LoadParcel
from repository.item.Item import Item

class ItemsTestCase(ParcelLoaderTestCase.ParcelLoaderTestCase):

    def testItems(self):

        """ Ensure we can create items within a parcel file
        """

        parcelDir = os.path.join(self.testdir, 'itemparcels')
        itemsDir = os.path.join(parcelDir, 'items')
        LoadParcel(itemsDir, '//parcels/items', parcelDir, self.rep)
        self.rep.commit()
        # PrintItem("//Schema", self.rep)
        # PrintItem("//parcels", self.rep)

        # Ensure the Parcel was created
        parcel = self.rep.find("//parcels/items")
        self.assertEqual(parcel.kind,
         self.rep.find("//Schema/Core/Parcel"))

        # Ensure testInstances were created
        testInstance1 = self.rep.find("//parcels/items/TestInstance1")
        self.assertEqual(testInstance1.kind,
         self.rep.find("//parcels/items/Kind2"))

        testInstance2 = self.rep.find("//parcels/items/TestInstance2")
        self.assertEqual(testInstance2.kind,
         self.rep.find("//parcels/items/Kind2"))

        self.assertEqual(testInstance1.RefAttribute, testInstance2)
        self.assertEqual(testInstance1.StringAttribute, "XYZZY")
        self.assertEqual(testInstance1.EnumAttribute, "B")

        kind1 = self.rep.find("//parcels/super/Kind1")
        self.assert_(kind1)
        kind2 = self.rep.find("//parcels/items/Kind2")
        self.assert_(kind2)
        self.assert_(kind1 in kind2.superKinds)
        self.assert_(kind2 in kind1.subKinds)

if __name__ == "__main__":
    unittest.main()
