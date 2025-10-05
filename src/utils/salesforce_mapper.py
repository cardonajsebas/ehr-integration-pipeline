from simple_salesforce import Salesforce

def build_sf_id_maps(sf: Salesforce) -> dict:
    """Queries Salesforce for various objects to build mapping dictionaries."""
    
    print("Building Salesforce ID maps...")
    sf_id_maps = {}

    account_query = """
        SELECT Id, EHR_Patient_Id__c
        FROM Account
        WHERE EHR_Patient_Id__c != null
    """
    accounts_data = sf.query_all(account_query)['records']
    sf_id_maps['patient_to_account'] = {rec['EHR_Patient_Id__c']: rec['Id'] for rec in accounts_data}

    resource_query = """
        SELECT Id, EHR_Resource_Id__c, Name
        FROM ServiceResource
        WHERE EHR_Resource_Id__c != NULL AND IsActive = True
    """
    resources_data = sf.query_all(resource_query)['records']
    sf_id_maps['practitioner_to_resource'] = {rec['EHR_Resource_Id__c']: rec['Id'] for rec in resources_data}
    sf_id_maps['resource_name_to_id'] = {rec['Name']: rec['Id'] for rec in resources_data}

    contact_query = """
        SELECT Id, Name
        FROM Contact
    """
    contact_data = sf.query_all(contact_query)['records']
    name_to_contact_id = {rec['Name']: rec['Id'] for rec in contact_data}

    sf_id_maps['practitioner_details'] = {}
    for rec in resources_data:
        resource_name = rec['Name']
        ehr_id = rec['EHR_Resource_Id__c']
        resource_id = rec['Id']
        contact_id = name_to_contact_id.get(resource_name)
        if contact_id:
            sf_id_maps['practitioner_details'][ehr_id] = {
                'Service_Resource__c': resource_id,
                'ContactId': contact_id
            }
        else:
            print(f"⚠️ Warning: No matching Contact found for ServiceResource Name: {resource_name}")

    territory_query = """
        SELECT Id, EHR_Location_Id__c
        FROM ServiceTerritory
        WHERE EHR_Location_Id__c != NULL AND IsActive = True
    """
    territories_data = sf.query_all(territory_query)['records']
    sf_id_maps['location_to_territory'] = {rec['EHR_Location_Id__c']: rec['Id'] for rec in territories_data}

    worktype_query = """
        SELECT Id, EHR_Work_Type_Id__c
        FROM WorkType
        WHERE EHR_Work_Type_Id__c != NULL
    """
    worktypes_data = sf.query_all(worktype_query)['records']
    sf_id_maps['worktype_code_to_id'] = {rec['EHR_Work_Type_Id__c']: rec['Id'] for rec in worktypes_data}

    print("Salesforce ID maps built successfully.")
    return sf_id_maps