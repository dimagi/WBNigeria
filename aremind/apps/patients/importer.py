import logging
from datetime import datetime
from lxml import etree

from django.core.exceptions import ValidationError
from django.db import transaction
from django.conf import settings

from rapidsms.models import Contact, Connection, Backend

from aremind.apps.patients import models as patients
from aremind.apps.patients.forms import PatientForm
from aremind.apps.groups.models import Group


logger = logging.getLogger('aremind.apps.patients.importer')


def parse_payload(payload):
    """ Parse entire XML payload sent from external database """
    try:
        parse_patient_list(payload)
    except Exception as e:
        payload.error_message = unicode(e)
        payload.status = 'error'
        payload.save()
        raise


@transaction.commit_on_success
def parse_patient_list(payload):
    """
    Parse entire XML payload sent from external database. All exceptions will 
    be caught, logged, and the database will be rolled back
    """
    logger.debug('Parsing payload #{0}'.format(payload.pk))
    try:
        root = etree.fromstring(payload.raw_data)
        logger.debug('Parsed payload #{0}'.format(payload.pk))
        for patient in root.iter("Table"):
            logger.debug('Found new patient node')
            parse_patient(patient, payload)
    except ValidationError as e:
        logger.exception(e)
        raise
    except Exception as e:
        logger.exception(e)
        raise ValidationError(e)


def parse_patient(node, payload):
    '''
    Creates a new patient_model entry (or updates if exists), also creating a Contact for that patient as needed.
    Returns False if there was an error parsing the xml patient data (the XML syntax is correct
    but we don't understand it or there was some other error).
    Returns True upon succesfully creating a Patient and related Contact
    '''
    # mapping of XML tags to Patient model fields
    valid_field_names = {
        "Subject_Number": 'subject_number',
        "Date_Enrolled": 'date_enrolled',
        "Mobile_Number": 'mobile_number',
        "Pin_Code": 'pin',
        "Next_Visit": 'next_visit',
        "Reminder_Time": 'reminder_time',
        "Daily_Doses": 'daily_doses',
        "Manual_Adherence": 'manual_adherence',
    }
    # convert XML structure into POST-like dictionary
    data = {}
    for field in node.getchildren():
        key = valid_field_names.get(field.tag, field.tag)
        data[key] = field.text
    # look up patient by subject number to see if this is an update
    subject = data.get('subject_number', '')
    instance = None
    if subject:
        logger.debug('Parsed patient {0}'.format(subject))
        try:
            instance = patients.Patient.objects.get(subject_number=subject)
            logger.debug("{0} found in database".format(subject))
        except patients.Patient.DoesNotExist:
            logger.debug("{0} doesn't exist in database".format(subject))
    # construct model form and see if data is valid
    form = PatientForm(data, instance=instance)
    if form.is_valid():
        logger.debug('{0} data is valid'.format(subject))
        patient = form.save(payload=payload)
        logger.debug('Saved patient {0}'.format(subject))
    else:
        logger.debug('Patient data is invalid')
        errors = dict((k, v[0]) for k, v in form.errors.items())
        errors['POST'] = unicode(data)
        raise ValidationError(errors)
