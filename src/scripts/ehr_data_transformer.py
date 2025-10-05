from src.api import EHR
import pandas as pd
import requests
import os
from dotenv import load_dotenv

load_dotenv()
ehr = EHR()
organization_id = os.getenv('HAPI_ORG_ID')

#Locations:
def locations_to_df(ehr:EHR, org_id:str) -> pd.DataFrame:
    """Normalize FHIR Location resources into a DataFrame."""
    
    response = ehr.get_resource('Location', f'organization={org_id}')
    locations = []
    for entry in response.get('entry', []):
        response = entry['resource']
        
        location_id = response.get('id')
        name = response.get('name')
        source = response.get('name')
        # Telecom (grab first phone if available)
        phone = None
        if 'telecom' in response:
            for t in response['telecom']:
                if t.get('system') == 'phone':
                    phone = t.get('value')
                    break
        status =  response.get('status')
        # Address:
        address = response.get('address', {})
        address_line = ' '.join(address.get('line', [])) if address else None
        city = address.get('city')
        state = address.get('state')
        zip_code = address.get('postalCode')

        locations.append({
            'location_id': location_id,
            'name': name,
            'phone': phone,
            'status': status,
            'address_line': address_line,
            'city': city,
            'state': state,
            'zip_code': zip_code
        })
    return pd.DataFrame(locations)

# Practitioners:
def providers_to_df(ehr:EHR, org_id:str, count: int = 50) -> pd.DataFrame:
    """Build dataframe with provider details (Practitioner + Role)."""
    
    roles = ehr.get_practitioner_roles(org_id, count)
    providers = []

    for entry in roles.get('entry', []):
        role = entry['resource']

        practitioner_ref = role.get('practitioner', {}).get('reference')
        if not practitioner_ref:
            continue
        practitioner_id = practitioner_ref.split('/')[-1]
        practitioner = ehr.get_practitioner(practitioner_id)

        # Practitioner data
        name_data = practitioner.get('name', [{}])[0]
        family = name_data.get('family')
        given = ' '.join(name_data.get('given', []))
        telecom = practitioner.get('telecom', [])
        phone = next((t['value'] for t in telecom if t.get('system') == 'phone'), None)
        email = next((t['value'] for t in telecom if t.get('system') == 'email'), None)
        # PractitionerRole data
        specialty = None
        if 'specialty' in role:
            coding = role['specialty'][0].get('coding', [])
            if coding:
                specialty = coding[0].get('display')
            else:
                specialty = role['specialty'][0].get('text')
        locations = [loc['reference'].split('/')[-1] for loc in role.get('location', [])]

        providers.append({
            'practitioner_id': practitioner_id,
            'first_name': given,
            'last_name': family,
            'phone': phone,
            'email': email,
            'specialty': specialty,
            'location_id': ', '.join(locations)
        })
    return pd.DataFrame(providers)

# Patients:
def patients_to_df(ehr:EHR, org_id:str) -> pd.DataFrame:
    """
    Extract all FHIR Patient resources for an organization and normalize them into a DataFrame.
    
    This function handles API pagination to retrieve the full list of patients.
    
    Parameters
    ----------
    ehr : EHR
        An instance of the EHR API client.
    org_id : str
        The ID of the managing organization to filter patients by.
    
    Returns
    -------
    pd.DataFrame
        A flattened DataFrame containing data for all patients.
    """
    url = f"{ehr.base_url}/Patient"
    params = {'organization': org_id}
    
    all_patient_entries = ehr.get_all_resources(url=url, params=params)
    
    patients = []
    for entry in all_patient_entries:
        response = entry.get('resource', {})
        
        patient_id = response.get('id')
        # Name (take first if multiple)
        name = None
        if 'name' in response and response['name']:
            given = ' '.join(response['name'][0].get('given', []))
            family = response['name'][0].get('family', '')
            name = f"{given} {family}".strip()
        # Birthdate & gender
        birth_date = response.get('birthDate')
        gender = response.get('gender')
        # Telecom (phone & email if available)
        phone, email = None, None
        for t in response.get('telecom', []):
            if t.get('system') == 'phone' and not phone:
                phone = t.get('value')
            elif t.get('system') == 'email' and not email:
                email = t.get('value')
        # Address (take first if multiple)
        address = response.get('address', [{}])[0]
        address_line = ' '.join(address.get('line', []))
        city = address.get('city')
        state = address.get('state')
        postal = address.get('postalCode')

        patients.append({
            'patient_id': patient_id,
            'name': name,
            'birth_date': birth_date,
            'gender': gender,
            'phone': phone,
            'email': email,
            'address_line': address_line,
            'city': city,
            'state': state,
            'postal_code': postal
        })
    return pd.DataFrame(patients)

# Appointments:
def appointments_to_df(appointment_entries: list) -> pd.DataFrame:
    """
    Normalize a list of FHIR Appointment entries into a clean DataFrame.

    Args:
        appointment_entries (list): A list of appointment 'entry' objects from the FHIR client.

    Returns:
        pd.DataFrame: A flattened DataFrame of appointment records.
    """
    appointments = []
    for entry in appointment_entries:
        resource = entry.get('resource', {})

        practitioner_id, patient_id, location_id = None, None, None
        for p in resource.get('participant', []):
            ref = p.get('actor', {}).get('reference', '')
            if ref.startswith('Practitioner/'):
                practitioner_id = ref.split('/')[-1]
            elif ref.startswith('Patient/'):
                patient_id = ref.split('/')[-1]
            elif ref.startswith('Location/'):
                location_id = ref.split('/')[-1]
        
        work_type_code = None
        service_types = resource.get('serviceType', [])
        if service_types and service_types[0].get('coding'):
            work_type_code = service_types[0]['coding'][0].get('code')
        
        appointments.append({
            'appointment_id': resource.get('id'),
            'patient_id': patient_id,
            'practitioner_id': practitioner_id,
            'location_id': location_id,
            'work_type_code': work_type_code,
            'status': resource.get('status'),
            'start': resource.get('start'),
            'end': resource.get('end')
        })
    return pd.DataFrame(appointments)

def process_appointments(ehr: EHR, org_id: str) -> pd.DataFrame:
    """
    Orchestrates the E-T (Extract-Transform) process for appointments.
    
    1. Extracts all appointments for an organization using the EHR client.
    2. Transforms the raw JSON response into a clean pandas DataFrame.
    """
    # EXTRACT: Get raw data from the API
    raw_appointments = ehr.get_all_appointments(organization_id=org_id)
    # TRANSFORM: Convert the raw data into a DataFrame
    appointments_df = appointments_to_df(raw_appointments)
    
    if 'start_time' in appointments_df.columns:
        appointments_df['start_time'] = pd.to_datetime(appointments_df['start_time'], errors='coerce')
        appointments_df['end_time'] = pd.to_datetime(appointments_df['end_time'], errors='coerce')
    return appointments_df


