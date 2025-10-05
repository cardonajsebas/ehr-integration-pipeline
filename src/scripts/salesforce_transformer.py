import pandas as pd
from zoneinfo import ZoneInfo

# --- Location/ServiceTerritory Transformer ---
def transform_locations_for_sf(locations_df: pd.DataFrame) -> pd.DataFrame:
    """Prepares the locations DataFrame for Salesforce ServiceTerritory object."""
    
    dict_rename = {
        'name': 'Name',
        'location_id': 'EHR_Location_Id__c',
        'address_line': 'Street',
        'city': 'City',
        'state': 'State',
        'zip_code': 'PostalCode'
    }
    locations_df = locations_df.rename(columns=dict_rename)
    locations_df['OperatingHoursId'] = '0OHbm000002EyftGAC'
    
    return locations_df[['Name', 'EHR_Location_Id__c', 'Street', 'City', 'State', 'PostalCode', 'OperatingHoursId']]

# --- Work Types Transformer ---
def transform_work_types_for_sf() -> pd.DataFrame:
    """Creates a DataFrame for standard Work Types."""
    
    WORK_TYPES = {
        "newpatient": {"code": "WT123", "display": "New Patient Consultation"},
        "followup": {"code": "WT456", "display": "Follow-up Visit"},
        "annual": {"code": "WT789", "display": "Annual Checkup"},
        "consult": {"code": "WT012", "display": "Consultation"},
        "nurse": {"code": "WT034", "display": "Nurse Visit"}
    }
    work_type_list = [
        {'Name': data['display'], 'EHR_Work_Type_Id__c': data['code']}
        for data in WORK_TYPES.values()
    ]
    work_types_df = pd.DataFrame(work_type_list)
    work_types_df['EstimatedDuration'] = 30
    work_types_df['DurationType'] = 'Minutes'
    
    return work_types_df[['Name', 'EstimatedDuration', 'DurationType', 'EHR_Work_Type_Id__c']]

# --- Provider/User Transformer ---
def transform_users_for_sf(providers_df: pd.DataFrame) -> pd.DataFrame:
    """Prepares provider data for Salesforce User object."""
    
    available_licenses = ['00ebm00000Dvu6OAAR', '00ebm00000Dvu6VAAR', '00ebm00000Dvu6GAAR', '00ebm00000Dvu6QAAR']   # Per dev sandbox limitations
    num_licenses = len(available_licenses)
    users_df = providers_df[['first_name', 'last_name', 'email']].copy()
    dict_rename = {
        'first_name': 'FirstName',
        'last_name': 'LastName',
        'email': 'Email'
    }
    users_df = users_df.rename(columns=(dict_rename))
    users_df['ProfileId'] = users_df.index.to_series().apply(lambda i: available_licenses[i % num_licenses])
    users_df['Username'] = users_df['Email']
    users_df['Alias'] = (users_df['FirstName'].str[0] + users_df['LastName'].str[:4]).str.lower().str.ljust(5, 'x')
    users_df['CommunityNickname'] = users_df['Alias']
    users_df['IsActive'] = True
    users_df['TimeZoneSidKey'] = 'America/New_York'
    users_df['EmailEncodingKey'] = 'UTF-8'
    users_df['LanguageLocaleKey'] = 'en_US'
    users_df['LocaleSidKey'] = 'en_US'
    
    return users_df

# --- Provider/ServiceResource Transformer ---
def transform_sresources_for_sf(providers_df: pd.DataFrame, user_id_map: dict) -> pd.DataFrame:
    """Prepares provider data for Salesforce ServiceResource object."""
    
    sresources_df = providers_df[['email', 'practitioner_id', 'specialty', 'first_name', 'last_name']].copy()
    sresources_df['Name'] = sresources_df['first_name'] + " " + sresources_df['last_name']
    sresources_df['EHR_Resource_Id__c'] = sresources_df['practitioner_id']
    sresources_df['Description'] = sresources_df['specialty']
    sresources_df['IsActive'] = True
    sresources_df['AccountId'] = '001bm00001CPgZKAA1'

    sresources_df['RelatedRecordId'] = sresources_df['email'].map(user_id_map)
    sresources_df_to_load = sresources_df.dropna(subset=['RelatedRecordId']).copy()
    records_skipped = len(sresources_df) - len(sresources_df_to_load)

    if records_skipped > 0:
        print(f"Skipping {records_skipped} ServiceResources because their corresponding User record failed to insert.")

    sresources_df_to_load = sresources_df_to_load[[
        'Name', 
        'EHR_Resource_Id__c', 
        'Description', 
        'IsActive', 
        'AccountId', 
        'RelatedRecordId'
    ]]
    
    return sresources_df_to_load

# --- Patient/Account Transformer ---
def transform_patients_for_sf(patients_df: pd.DataFrame) -> pd.DataFrame:
    """Prepares patient data for Salesforce Account object."""
    
    patients_df[['First_Name__c', 'Last_Name__c']] = patients_df['name'].str.split(" ", n=1, expand=True)
    dict_rename = {
        'name': 'Name',
        'birth_date': 'Date_of_Birth__c',
        'patient_id': 'EHR_Patient_Id__c',
        'address_line': 'Address_Line__c',
        'city': 'City__c',
        'state': 'State__c',
        'postal_code': 'Postal_Code__c',
        'phone': 'Phone',
        'email': 'Email__c'
    }
    patients_df = (patients_df.drop(columns=['gender']).rename(columns=(dict_rename)))
    
    return patients_df

# --- Appointment/ServiceAppointment Transformer ---
def transform_appointments_for_sf(appointments_df: pd.DataFrame, sf_id_maps: dict) -> pd.DataFrame:
    """
    Maps EHR IDs to Salesforce IDs and prepares the DataFrame for ServiceAppointment insertion.
    (This is the `prepare_service_appointments` function, moved from salesforce_functions.py)
    """
    
    appointments_df = appointments_df.rename(columns={'appointment_id': 'EHR_Appointment_Id__c', 'status': 'Status'})
    appointments_df['Status'] = appointments_df['Status'].replace({'booked': 'Scheduled', 'cancelled': 'Canceled', 'fulfilled': 'Completed'})

    # Scheduling Start and End times
    appointments_df['start'] = appointments_df['start'].str.replace('Z', '', regex=False).str.replace('00Z', '', regex=False)
    appointments_df['end'] = appointments_df['end'].str.replace('Z', '', regex=False).str.replace('00Z', '', regex=False)

    appointments_df['start'] = pd.to_datetime(appointments_df['start'], errors='coerce')
    appointments_df['end'] = pd.to_datetime(appointments_df['end'], errors='coerce')

    appointments_df['start'] = appointments_df['start'].dt.tz_localize(None)
    appointments_df['end'] = appointments_df['end'].dt.tz_localize(None)

    appointments_df['start'] = appointments_df['start'].dt.tz_localize(ZoneInfo('America/New_York'))
    appointments_df['end'] = appointments_df['end'].dt.tz_localize(ZoneInfo('America/New_York'))

    appointments_df['start_utc'] = appointments_df['start'].dt.tz_convert('UTC')
    appointments_df['end_utc'] = appointments_df['end'].dt.tz_convert('UTC')

    appointments_df['SchedStartTime'] = appointments_df['start_utc'].dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    appointments_df['SchedEndTime'] = appointments_df['end_utc'].dt.strftime('%Y-%m-%dT%H:%M:%SZ')

    appointments_df['ParentRecordId'] = appointments_df['patient_id'].map(sf_id_maps['patient_to_account'])

    appointments_df['resource_details'] = appointments_df['practitioner_id'].map(sf_id_maps['practitioner_details'])
    
    appointments_df['Service_Resource__c'] = appointments_df['resource_details'].apply(lambda x: x['Service_Resource__c'] if isinstance(x, dict) else None)
    
    appointments_df['ContactId'] = appointments_df['resource_details'].apply(lambda x: x['ContactId'] if isinstance(x, dict) else None)
    
    appointments_df['ServiceTerritoryId'] = appointments_df['location_id'].map(sf_id_maps['location_to_territory'])
    appointments_df['WorkTypeId'] = appointments_df['work_type_code'].map(sf_id_maps['worktype_code_to_id'])

    required_cols = ['ParentRecordId', 'Service_Resource__c', 'ContactId', 'WorkTypeId']
    sa_df_ready = appointments_df.dropna(subset=required_cols).copy()
    
    skipped_count = len(appointments_df) - len(sa_df_ready)
    if skipped_count > 0:
        print(f"⚠️ Skipped {skipped_count} Service Appointments due to missing mappings (Patient, Resource, Contact, or Work Type).")
    
    final_cols = [
        'EHR_Appointment_Id__c', 'ParentRecordId', 'Service_Resource__c', 'ContactId', 'ServiceTerritoryId', 'WorkTypeId',
        'SchedStartTime', 'SchedEndTime', 'Status'
    ]
    
    return sa_df_ready[final_cols]



