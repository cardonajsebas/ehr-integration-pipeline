from src.api import EHR
from projects.ehr_integration.src.utils.mock_data import *
import time
import os
from dotenv import load_dotenv

load_dotenv()
ehr = EHR()
organization_id = os.getenv('HAPI_ORG_ID')

# Organization
def load_organization(ehr:EHR, new_org):
    """Load custom organization into HAPI FHIR."""
    
    new_org = {
        'resourceType': 'Organization',
        'name': 'JSC Health Integration Demo',
        'alias': ['FHIR Portfolio Project'],
        'telecom': [
            {'system': 'phone', 'value': '+1-555-000-0000'},
            {'system': 'email', 'value': 'info@demo-health.org.invalid'}
        ],
        'address': [{
            'line': ['123 Demo Street'],
            'city': 'Miami',
            'state': 'FL',
            'postalCode': '33186',
            'country': 'US'
        }],
        'active': True
    }
    response = ehr.post_organization(new_org)
    print("Created organization: ", response.get('id'))

# Location
def load_location(ehr:EHR, new_location):
    """Load custom location into HAPI FHIR."""
    
    new_location = {
        'resourceType': 'Location',
        'name': 'JSC South Miami Clinic',
        'status': 'active',
        'telecom': [{'system': 'phone', 'value': '305-111-2233'}],
        'address': {
            'line': ['12345 Sunset Drive'],
            'city': 'Miami',
            'state': 'FL',
            'postalCode': '33156'
        },
        'managingOrganization': {
            'reference': f'Organization/{organization_id}'  # <-- New Org Id
        }
    }
    response = ehr.post_location(new_location)
    print("Created location: ", response.get('id'))

# Practitioner
def load_practitioner(ehr:EHR, new_practitioner):
    """Load custom practitioner into HAPI FHIR."""
    
    new_practitioner = {
        'resourceType': 'Practitioner',
        'name': [
            {
                "use": "official",
                'family': "Testing",
                "given": ["Sebastian"]
            }
        ],
        "telecom": [
            {"system": "phone", "value": "305-123-4567", "use": "work"},
            {"system": "email", "value": "stest@demo-health.org.invalid", "use": "work"}
        ],
        "address": [
            {
                "line": ["123 Clinic St"],
                "city": "Miami",
                "state": "FL",
                "postalCode": "33193"
            }
        ],
        "gender": "male",
        'active': True
    }
    response = ehr.post_practitioner(new_practitioner)
    print("Created practitioner: ", response.get('id'))

# Practitioner_Role
def load_practitioner_role(ehr:EHR, role, practitioner_id, organization_id, location_id):
    """Load Practitioner_Role into HAPI FHIR."""
    
    role = {
        'resourceType': 'PractitionerRole',
        'practitioner': {
            'reference': f'Practitioner/{practitioner_id}'
        },
        'organization': {
            'reference': f'Organization/{organization_id}'
        },
        'location': {
            'reference': f'Location/{location_id}'
        },
        'specialty': [
            {
                'coding': [
                    {
                        'system': 'https://taxonomy.nucc.org/',
                        'code': '208D00000X',
                        'display': 'General Practice Physician'
                    }
                ],
                'text': 'General Practice Physician'
            }
        ],
        'active': True
    }
    response = ehr.post_practitioner_role(role)
    print("Created practitioner role: ", response.get('id'))

# Patients
def load_patients(ehr:EHR, patients_df):
    """Load generated patients DataFrame into HAPI FHIR."""
    
    for _, row in patients_df.iterrows():
        patient = {
            'resourceType': 'Patient',
            'name': [{'use': 'official', 'family': row['last_name'], 'given': [row['first_name']]}],
            'gender': row['gender'],
            'birthDate': row['birthDate'],
            'telecom': [
                {'system': 'phone', 'value': row['phone'], 'use': 'mobile'},
                {'system': 'email', 'value': row['email'], 'use': 'home'},
            ],
            'address': [row['address']],
            'managingOrganization': {'reference': f"Organization/{row['organization_id']}"},
        }

        response = ehr.post_patient(patient)
        print("Created patient: ", response.get("id"))

# Appointments
def load_appointments(ehr:EHR, appointments_df, work_types:dict, sleep_time:float = 0.5):
    """Load generated appointments DataFrame into HAPI FHIR."""
    
    total = len(appointments_df)
    print(f"Starting to POST {total} appointments...")
    responses = []

    for i, row in appointments_df.iterrows():
        try:
            appt = make_appointment_dict(row, work_types)
            response = ehr.post_appointment(appt)
            fhir_id = response.get('id')
            responses.append({'id': fhir_id, 'status': 'success'})
            print(f"[{i+1}/{total}] ✅ Created Appointment (ID: {fhir_id})")
        except Exception as e:
            responses.append({'error': str(e), 'status': 'failed'})
            print(f"[{i+1}/{total}] ❌ Error: {e}")

        time.sleep(sleep_time)

    print("Finished posting appointments.")
    return responses


