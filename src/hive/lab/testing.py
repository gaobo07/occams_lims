from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from plone.app.testing import IntegrationTesting
from plone.app.testing import FunctionalTesting
import plone.testing
from zope.configuration import xmlconfig
from datetime import date

from hive.lab import model
from occams.datastore.testing import OCCAMS_DATASTORE_FIXTURE


try:
    # Prefer the future naming convention 
    from avrc.aeh.testing import OCCAMS_CLINICAL_FIXTURE
except ImportError:
    # Still not up-to-date, use the original
    from avrc.aeh.testing import CLINICAL_FIXTURE as OCCAMS_CLINICAL_FIXTURE


class OccamsLabModelLayer(plone.testing.Layer):
    """
    DataBase application layer for tests.
    """
    defaultBases = (OCCAMS_DATASTORE_FIXTURE,)

    def testSetUp(self):
        """
        """
        session = self['session']
        dummy_patient = model.Patient(
            our="XXX-XXX",
             zid=234567890
             )
        session.add(dummy_patient)
        session.flush()
        self['dummy_patient'] = dummy_patient

        dummy_study = model.Study(
            name="Dummy Study",
             title=u"Dummy Study",
             code=u"000",
             consent_date=date.today(),
             zid=345678901
             )
        session.add(dummy_study)
        session.flush()
        self['dummy_study'] = dummy_study

        dummy_cycle = model.Cycle(
            name="Dummy Cycle",
             title=u"Dummy Cycle",
             week=u"0",
             study=dummy_study,
             zid=456789012
             )
        session.add(dummy_cycle)
        session.flush()
        self['dummy_cycle'] = dummy_cycle

class OccamsLabLayer(PloneSandboxLayer):

    defaultBases = (OCCAMS_CLINICAL_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load ZCML
        import hive.lab as package
        xmlconfig.file('configure.zcml', package, context=configurationContext)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'hive.lab:default')

OCCAMS_LAB_MODEL_FIXTURE = OccamsLabModelLayer()

OCCAMS_LAB_FIXTURE= OccamsLabLayer()

OCCAMS_LAB_INTEGRATION_TESTING = IntegrationTesting(
    bases=(OCCAMS_LAB_FIXTURE,),
    name="OccamsLab:Integration"
    )

OCCAMS_LAB_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(OCCAMS_LAB_FIXTURE,),
    name='OccamsLab:Functional'
    )
