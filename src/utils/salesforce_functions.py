import pandas as pd
from simple_salesforce import Salesforce


# Data loading functions
def load_data_to_salesforce_bulk(sf_connection: Salesforce, dataframe: pd.DataFrame, sf_object_name: str) -> dict:
    """
    Loads records from a pandas DataFrame into a specified Salesforce object 
    using the simple_salesforce Bulk API 'create' method.

    Args:
        sf_connection: An active simple_salesforce.Salesforce connection object.
        dataframe: The pandas DataFrame containing the data to load.
                    Column names must match Salesforce API names (case-sensitive).
        sf_object_name: The Salesforce API name of the object (e.g., 'Account', 'CustomObject__c').

    Returns:
        A dictionary summarizing the results (success count, failure count, and a list of failed records).
    """
    
    if dataframe.empty:
        return {"success_count": 0, "failure_count": 0, "status": "DataFrame is empty, no records loaded."}

    records_to_load = dataframe.to_dict('records')
    total_records = len(records_to_load)
    
    print(f"Submitting bulk job for {total_records} records into {sf_object_name}...")

    try:
        results = sf_connection.bulk.__getattr__(sf_object_name).create(records_to_load)
        
        success_count = 0
        failed_records_details = []
        
        for i, result in enumerate(results):
            if result.get('success'):
                success_count += 1
            else:
                error_details = {
                    'record_index': i,
                    'record_data': records_to_load[i],
                    'errors': result.get('errors')
                }
                failed_records_details.append(error_details)
        
        failure_count = total_records - success_count
        
        print(f"✅ Job complete for {sf_object_name}.")
        print(f"   Successes: {success_count}, Failures: {failure_count}")

        return {
            "success_count": success_count,
            "failure_count": failure_count,
            "failed_records": failed_records_details,
            "status": "Job completed successfully."
        }

    except Exception as e:
        print(f"❌ An error occurred during the bulk load for {sf_object_name}: {e}")
        return {
            "success_count": 0,
            "failure_count": total_records,
            "status": f"Critical error during job submission: {e}"
        }

def load_data_to_salesforce_rest(sf_connection: Salesforce, dataframe: pd.DataFrame, sf_object_name: str) -> dict:
    """
    Loads records from a pandas DataFrame into a specified Salesforce object 
    using the simple_salesforce REST API 'create' method (single record inserts).
    and returns details of successful and failed inserts.
    """
    
    if dataframe.empty:
        return {"success_count": 0, "failure_count": 0, "status": "DataFrame is empty, no records loaded.", "successful_records": []}

    records_to_load = dataframe.to_dict('records')
    total_records = len(records_to_load)
    success_count = 0
    failed_records_details = []
    successful_records_details = []
    
    print(f"Submitting REST job for {total_records} records into {sf_object_name}...")

    # Access the specific object's REST endpoint
    sf_object_rest = sf_connection.__getattr__(sf_object_name)

    for i, record in enumerate(records_to_load):
        try:
            # Execute the REST API 'create' method
            result = sf_object_rest.create(record)
            success_count += 1
            # Store details of the successful record
            successful_records_details.append({
                'original_data': record,
                'sf_id': result.get('id'), # <-- Capture the generated Salesforce Id
                'index': i
            })
            
        except Exception as e:
            # Log the error details
            error_details = {
                'record_index': i,
                'record_data': record,
                'errors': str(e)
            }
            failed_records_details.append(error_details)
    
    failure_count = total_records - success_count
    
    print(f"✅ REST Job complete for {sf_object_name}.")
    print(f"   Successes: {success_count}, Failures: {failure_count}")

    return {
        "success_count": success_count,
        "failure_count": failure_count,
        "failed_records": failed_records_details,
        "successful_records": successful_records_details,
        "status": "Job completed successfully."
    }




