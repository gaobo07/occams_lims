from plone.dexterity import content
import zope.interface
from zope.schema.fieldproperty import FieldProperty
import zope.component
from zope.app.intid.interfaces import IIntIds
from datetime import date
from avrc.data.store.lab import Specimen
from avrc.data.store.lab import Aliquot


from hive.lab.interfaces.specimen import ISpecimenBlueprint
from hive.lab.interfaces.aliquot import IAliquotBlueprint


class SpecimenBlueprint(content.Container):
    zope.interface.implements(ISpecimenBlueprint)
    __doc__ = ISpecimenBlueprint.__doc__

    specimen_type = FieldProperty(ISpecimenBlueprint["specimen_type"])

    default_tubes = FieldProperty(ISpecimenBlueprint["default_tubes"])

    tube_type = FieldProperty(ISpecimenBlueprint["tube_type"])

    destination = FieldProperty(ISpecimenBlueprint["destination"])

    def createSpecimen(self, subject_zid, protocol_zid, date_collected):
        """
        Build a set of keyword arguements and pass back a specimen matching this blueprint
        """
        intids = zope.component.getUtility(IIntIds)
        blueprint_zid = intids.getId(self)
        
        kwargs = {}
        kwargs['subject_zid'] = subject_zid
        kwargs['protocol_zid'] = protocol_zid
        kwargs['state'] = u'pending-draw' 
        kwargs['date_collected'] = date_collected
        kwargs['specimen_type'] = self.specimen_type
        kwargs['destination'] = self.destination
        kwargs['tubes'] = self.default_tubes
        kwargs['tube_type'] = self.tube_type

        return Specimen(**kwargs)
        
    def aliquotSpecimen(self, specimen):
        """
        Loop through the aliquot in this folder, and 
        create aliquots.
        """
        for blueprint in self.folderContents({'portal_type':'IAliquotBlueprint'}):
            blueprint.createAliquot(specimen)
        setattr(specimen, 'state', u'aliquoted')
        # Get the transaction and commit it?

class AliquotBlueprint(content.Item):
    zope.interface.implements(IAliquotBlueprint)
    __doc__ = IAliquotBlueprint.__doc__
    
    default_count = FieldProperty(IAliquotBlueprint["default_count"])

    aliquot_type = FieldProperty(IAliquotBlueprint["aliquot_type"])

    volume = FieldProperty(IAliquotBlueprint["volume"])
        
    cell_amount = FieldProperty(IAliquotBlueprint["cell_amount"])
        
    storage_site = FieldProperty(IAliquotBlueprint["storage_site"])
        
    special_instructions = FieldProperty(IAliquotBlueprint["special_instructions"])


    def createAliquot(self, specimen, store_date):
        """
        Build a set of keyword arguements and pass back a specimen matching this blueprint
        """
        if store_date is None:
            store_date = date()
        # intids = zope.component.getUtility(IIntIds)
#         blueprint_zid = intids.getId(self)
#         
        kwargs={}
        kwargs['specimen_dsid'] = 
        kwargs['type'] = self.aliquot_type
        kwargs['volume'] = self.volume
        kwargs['cell_amount'] = self.cell_amount
        kwargs['store_date'] = store_date
        kwargs['storage_site'] = self.storage_site
        kwargs['thawed_num'] = 0
        kwargs['special_instruction'] = self.special_instructions
        
        obj.freezer = context.freezer
        obj.rack = context.rack
        obj.box = context.box
        obj.notes = context.notes
        
        aliquot_list=[]
        for i in self.default_count:
            aliquot_list.append(Aliquot(**kwargs))
            
        return aliquot_list