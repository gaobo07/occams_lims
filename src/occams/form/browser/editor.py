from copy import copy
from datetime import datetime
from decimal import Decimal
import json
import os.path

from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from zope.publisher.browser import BrowserView

from collective.z3cform.datagridfield import DataGridFieldFactory
from collective.beaker.interfaces import ISession
from plone.z3cform import layout
import z3c.form.form
import z3c.form.button
import z3c.form.field
import z3c.form.group
from z3c.form.interfaces import HIDDEN_MODE
from z3c.form.interfaces import INPUT_MODE
from  z3c.form.browser.text import TextFieldWidget
from avrc.data.store.interfaces import IDataStore

from occams.form import MessageFactory as _
from occams.form.interfaces import SESSION_KEY
from occams.form.interfaces import IEditableForm
from occams.form.interfaces import IEditableField
from occams.form.interfaces import IEditableBooleanField
from occams.form.interfaces import IEditableDateField
from occams.form.interfaces import IEditableDateTimeField
from occams.form.interfaces import IEditableIntegerField
from occams.form.interfaces import IEditableDecimalField
from occams.form.interfaces import IEditableStringField
from occams.form.interfaces import IEditableTextField
from occams.form.interfaces import IEditableObjectField
from occams.form.interfaces import typesVocabulary
from occams.form.browser.widgets import fieldWidgetMap
from occams.form.browser.widgets import TextAreaFieldWidget
from occams.form.serialize import serializeForm
from occams.form.serialize import fieldFactory
from occams.form.serialize import tokenize


editableFieldSchemaMap = dict(
    boolean=IEditableBooleanField,
    date=IEditableDateField,
    datetime=IEditableDateTimeField,
    decimal=IEditableDecimalField,
    integer=IEditableIntegerField,
    string=IEditableStringField,
    text=IEditableTextField,
    object=IEditableObjectField,
    )

STATUS_NOT_MODIFIED = 304
STATUS_SUCCESS = 200


class SchemaEditForm(z3c.form.form.EditForm):
    """
    Renders the form for editing, using a subform for the fields editor.
    """

    template = ViewPageTemplateFile('editor_templates/schema.pt')

    # Certain sub-form components (*cough* datagridfield) don't handle inline
    # validation very well, so we're turning it off on the entire edit for.
    ignoreRequest = True

    # The form's metadata properties (title, description, storage, etcc...)
    fields = z3c.form.field.Fields(IEditableForm).omit('name')

    # Override the tiny text area wiget with a nice bigger one
    fields['description'].widgetFactory = TextAreaFieldWidget

    # The form's entry fields (the ones the user enters data into when filling out)
    fieldsSubForm = None

    @property
    def prefix(self):
        return 'occams-form-master'

    def getContent(self):
        return ISession(self.request)[SESSION_KEY]

    def update(self):
        repository = self.context.getParentNode()
        formName = self.context.item.name
        formVersion = None

        # Load the form into the session, which is what we'll be using for
        # intermediary data storage while the form is being modified.
        browserSession = ISession(self.request)
        form = IDataStore(repository).schemata.get(formName, formVersion)
        browserSession[SESSION_KEY] = serializeForm(form)
        browserSession.save()

        # Render the fields editor form
        self.fieldsSubForm = FieldsForm(self.context, self.request)
        self.fieldsSubForm.update()
        super(SchemaEditForm, self).update()

    @z3c.form.button.buttonAndHandler(_('Cancel'), name='cancel')
    def handleCancel(self):
        """
        Cancels form changes.
        """
        # Delete the item in the session, leaving everything else intact
        browserSession = ISession(self.request)
        browserSession.delete()

    @z3c.form.button.buttonAndHandler(_(u'Complete'), name='submit')
    def handleComplete(self):
        """
        Save the form changes
        """
        # This is going to be huge
        return


class SchemaEditFormPloneView(layout.FormWrapper):
    """
    Form wrapper for Z3C so that it appears within Plone nicely
    """

    form = SchemaEditForm

    @property
    def label(self):
        return _(u'Edit: %s (%s)') % (self.context.item.title, self.context.item.name)


class FieldsForm(z3c.form.group.GroupForm, z3c.form.form.Form):
    """
    Fields editor form.

    A note on sub-objects: There currently seems to be too many caveats
    surrounding object widgets (see ``z3c.form.object``). Given that, we
    will be using z3c group forms to represent sub objects.

    Uses Browser Session for data.
    """

    template = ViewPageTemplateFile('editor_templates/fields.pt')

    ignoreContext = True
    ignoreRequest = True

    # The form's fields, initialized in the constructor
    groups = []

    def types(self):
        """
        Template helper for types
        """
        return typesVocabulary

    def update(self):
        groups = []
        objectFilter = lambda x: x['schema'] is not None
        orderSort = lambda i: i['order']

        formData = ISession(self.request)[SESSION_KEY]

        defaultFieldsetData = dict(interface=formData['name'], schema=formData)
        groups.append(Fieldset(defaultFieldsetData, self.request, self))

        fields = formData['fields']
        objects = sorted(filter(objectFilter, fields.values()), key=orderSort)

        for objectData in objects:
            groups.append(Fieldset(objectData, self.request, self))

        self.groups = groups
        super(FieldsForm, self).update()


class Fieldset(z3c.form.group.Group):
    """
    A generic group for fields of type Object to represent as a fieldset.
    This class can also be used for the top level form to be represented as a
    fieldset (has no referencing field).
    """

    @property
    def prefix(self):
        return self.context.get('name') or ''

    @property
    def label(self):
        return self.context.get('title')

    @property
    def description(self):
        return self.context.get('description')

    @property
    def parentUrl(self):
        return self.parentForm.context.getParentNode().absolute_url()

    def fieldContext(self, field=None):
        if field is None:
            fieldContext = self.context
        else:
            fieldContext = self.context['schema']['fields'][field.getName()]
        return fieldContext

    def url(self, field=None):
        # No field within the object specifiexd, process actual object field
        fieldContext = self.fieldContext(field)
        formName = fieldContext.get('interface') or ''
        fieldName = fieldContext.get('name') or ''
        return os.path.join(self.parentUrl, formName, fieldName)

    def editUrl(self, field=None):
        """
        Template helper for the edit URL of a field or group
        """
        return os.path.join(self.url(field), '@@edit')

    def deleteUrl(self, field=None):
        """
        Template helper for the delete URL of a field or group
        """
        return os.path.join(self.url(field), '@@delete')

    def type(self, field=None):
        """
        Template helper for retrieving the type of a field or group
        """
        return self.fieldContext(field).get('type')

    def version(self, field=None):
        """
        Template helper for retrieving the version of a field or group
        """
        versionRaw = self.fieldContext(field).get('version') or datetime.now()
        version = versionRaw.strftime('%Y-%m-%d')
        return version

    def update(self):
        fields = z3c.form.field.Fields()
        for fieldContext in sorted(self.context['schema']['fields'].values(), key=lambda x: x['order']):
            if fieldContext['type'] != 'object':
                schemaField = fieldFactory(fieldContext)
                fields += z3c.form.field.Fields(schemaField)
                widgetFactory = fieldWidgetMap.get(schemaField.__class__)
                if widgetFactory:
                    fields[schemaField.getName()].widgetFactory = widgetFactory
        self.fields = fields
        super(Fieldset, self).update()

    def updateWidgets(self):
        """
        Configure widgets, we'll mostly be disabling to prevent data entry.
        """
        super(Fieldset, self).updateWidgets()
        # Disable fields since we're not actually entering data
        for widget in self.widgets.values():
            widget.disabled = 'disabled'


class FieldFormHelper(object):

    typeName = None

    def getFormData(self):
        parent = self.context.getParentNode()
        browserSession = ISession(self.request)
        formData = browserSession[SESSION_KEY]

        if hasattr(parent, 'item'):
            formName = parent.item.name
            fieldName = self.context.item.name
        else:
            formName = self.context.item.name
            fieldName = None

        if fieldName not in formData['fields']:
            for name, fieldset in formData['fields'].items():
                schemaData = fieldset['schema']
                if schemaData is not None and schemaData['name'] == formName:
                    formData = schemaData
                    break
        return formData

    def getFieldData(self):
        parent = self.context.getParentNode()
        if not hasattr(parent, 'item'):
            fieldData = None
        else:
            fieldData = self.getFormData()['fields'][self.context.item.name]
        return fieldData


class FieldFormInputHelper(FieldFormHelper):

    def __init__(self, context, request):
        super(FieldFormInputHelper, self).__init__(context, request)
        schema = editableFieldSchemaMap[self.typeName]
        self.fields = z3c.form.field.Fields(schema)
        self.fields['description'].widgetFactory = TextAreaFieldWidget
        if 'choices' in self.fields:
            self.fields['choices'].widgetFactory = DataGridFieldFactory

    def datagridInitialise(self, subform, widget):
        widget.allow_reorder = True
        # This is very wonky and needs work on their side
        widget.auto_append = True
        widget.allow_insert = True
        widget.allow_delete = True

        if self.typeName == 'boolean':
            subform.fields['value'].widgetFactory = TextFieldWidget
            widget.allow_insert = False
            widget.allow_delete = False

    def datagridUpdateWidgets(self, subform, widgets, widget):
        if self.typeName == 'boolean':
            widgets['value'].readonly = 'readonly'

    def move(self, fieldName, position):
        changes = dict()
        changed = list()
        formData = self.getFormData()
        for field in sorted(formData['fields'].values(), key=lambda i: i['order']):
            # Move the field to here
            if position == field['order']:
                formData['fields'][fieldName]['order'] = position
                changed.append(fieldName)

            # Reorder anything following
            if field['name'] != fieldName and position >= field['order']:
                changed.append(fieldName)
                field['order'] += 1

        if changes:
            changes[self.fields['order'].interface] = changed
        return changes

    def processChoices(self, data):
        # This is also similar to what is done in the edit form's apply
        # Do some extra work with choices on fields we didn't ask for.
        # Mostly things that are auto-generated for the user since it we
        # have never used and it they don't seem very relevant
        # (except, say, order)
        if 'choices' in data:
            for order, choice in enumerate(data['choices'], start=0):
                if choice.get('value') is None:
                    choice['value'] = choice['title']
                choice['name'] = tokenize(choice['value'])
                choice['order'] = order

class FieldPreview(FieldFormHelper, z3c.form.form.Form):

    ignoreRequest = True

    @property
    def label(self):
        return 'Preview: %s' % self.context.item.name

    def updateWidgets(self):
        fieldData = self.getFieldData()
        schemaField = fieldFactory(fieldData)
        self.fields = z3c.form.field.Fields(schemaField)
        widgetFactory = fieldWidgetMap.get(schemaField.__class__)
        if widgetFactory:
            self.fields[schemaField.getName()].widgetFactory = widgetFactory
        super(FieldPreview, self).updateWidgets()
        for widget in self.widgets.values():
            widget.disabled = 'disabled'


class FieldJsonView(FieldFormHelper, BrowserView):

    def __call__(self):
        data = copy(self.getFieldData())
        if data['schema']:
            del data['schema']
        if data['type'] != 'object':
            data['view'] = FieldPreview(self.context, self.request)()
        else:
            data['view'] = None
        data['version'] = data['version'].date().isoformat()
        if data['choices']:
            for choice in data['choices']:
                if isinstance(choice['value'], Decimal):
                    choice['value'] = str(choice['value'])
        return json.dumps(data)


class BaseFieldAddForm(FieldFormInputHelper, z3c.form.form.AddForm):
    """
    Optionally takes a request variable ``order`` to preset where the
    field will be added (otherwise at the end of the form)
    """
    z3c.form.form.extends(z3c.form.form.AddForm)

    _newItem = None

    @property
    def label(self):
        return _('New %s Field') % typesVocabulary.getTermByToken(self.typeName).title

    def updateWidgets(self):
        self.buttons = self.buttons.select('cancel', 'add')
        if 'order' in self.request:
            self.fields['order'].mode = HIDDEN_MODE
        else:
            self.fields['order'].mode = INPUT_MODE
        super(BaseFieldAddForm, self).updateWidgets()
        self.widgets['order'].value = self.request.get('order')

    def create(self, data):
        result = copy(data)
        formData = self.getFormData()
        self.processChoices(result)

        position = data['order']
        fieldCount = len(formData['fields'])
        if position is None or position > fieldCount:
            position = fieldCount
        elif position is None or position < 0:
            position = 0

        schema = None

        if self.typeName == 'object':
            schema = dict(
                name=result['schemaName'],
                title=result['title'],
                description='auto-generated class',
                version=datetime.now(),
                fields=dict(),
                )

        del result['schemaName']

        result.update(dict(
            version=datetime.now(),
            type=self.typeName,
            interface=self.context.item.name,
            schema=schema,
            choices=None,
            order=position,
            ))
        return result

    def add(self, item):
        formData = self.getFormData()
        formData['fields'][item['name']] = item
        self.move(item['name'], item['order'])
        self._newItem = item

    def nextURL(self):
        url = self.context.absolute_url()
        if self._newItem is not None:
            url = os.path.join(url, self._newItem['name'], '@@json')
        return url

    @z3c.form.button.buttonAndHandler(_(u'Cancel'), name='cancel')
    def handleCancel(self, action):
        self._finishedAdd = True


class BooleanFieldAddForm(BaseFieldAddForm):

    typeName = 'boolean'

    def updateWidgets(self):
        super(BooleanFieldAddForm, self).updateWidgets()
        self.widgets['choices'].value = [
            dict(title=u'False', value=False),
            dict(title=u'True', value=True),
            ]


class DateFieldAddForm(BaseFieldAddForm):

    typeName = 'date'


class DateTimeFieldAddForm(BaseFieldAddForm):

    typeName = 'datetime'


class DecimalFieldAddForm(BaseFieldAddForm):

    typeName = 'decimal'


class IntegerFieldAddForm(BaseFieldAddForm):

    typeName = 'integer'


class StringFieldAddForm(BaseFieldAddForm):

    typeName = 'string'


class TextFieldAddForm(BaseFieldAddForm):

    typeName = 'text'


class ObjectFieldAddForm(BaseFieldAddForm):

    typeName = 'object'


class FieldEditForm(FieldFormInputHelper, z3c.form.form.EditForm):
    z3c.form.form.extends(z3c.form.form.EditForm)

    @property
    def typeName(self):
        return self.context.item.type

    @property
    def label(self):
        return _(u'Edit: %s') % self.context.item.name

    def getContent(self):
        return self.getFieldData()

    def updateWidgets(self):
        self.buttons = self.buttons.select('cancel', 'apply')
        self.fields['order'].mode = HIDDEN_MODE
        super(FieldEditForm, self).updateWidgets()
        self.widgets['name'].readonly = 'readonly'

    @z3c.form.button.buttonAndHandler(_(u'Cancel'), name='cancel')
    def handleCancel(self, action):
        parent = self.context.getParentNode()
        self.request.response.redirect(os.path.join(parent.absolute_url()))

    def applyChanges(self, data):
        self.processChoices(data)
        # Now do the default changes
        changes = super(FieldEditForm, self).applyChanges(data);
        if changes:
            self.getContent()['version'] = datetime.now()
        self.request.response.redirect(os.path.join(self.context.absolute_url(), '@@json'))


class FieldOrderForm(FieldFormInputHelper, z3c.form.form.Form):
    """
    AJAX form for reordering a field.
    """

    fields = z3c.form.field.Fields(IEditableField).select('order')

    @property
    def typeName(self):
        return self.context.item.type

    @property
    def label(self):
        return _(u'Reorder: %s') % self.context.item.name

    def applyChanges(self, data):
        fieldName = self.context.item.name
        changes = self.move(fieldName, data['order'])
        if changes:
            self.request.response.setStatus(STATUS_SUCCESS)
        else:
            self.request.response.setStatus(STATUS_NOT_MODIFIED)


class FieldDeleteForm(FieldFormHelper, z3c.form.form.Form):
    """
    Delete confirmation form.
    TODO: It would be nice to have both AJAX and BROWSER mode,
    currently this form assumes it's being called via AJAX.
    """

    template = ViewPageTemplateFile('editor_templates/delete.pt')

    @property
    def typeName(self):
        return self.context.item.type

    @property
    def label(self):
        return _(u'Delete: %s') % self.context.item.name

    @z3c.form.button.buttonAndHandler(_(u'Cancel'), name='cancel')
    def handleCancel(self, action):
        self.request.response.setStatus(STATUS_NOT_MODIFIED);

    @z3c.form.button.buttonAndHandler(_(u'Yes, I\'m sure'), name='delete')
    def handleDelete(self, action):
        formData = self.getFormData()
        fieldName = self.context.item.name
        del formData['fields'][fieldName]
        self.request.response.setStatus(STATUS_SUCCESS);
