# 1. Imports - Clean and organized by function
from src.api import EHR
from src.scripts.ehr_data_processor import locations_to_df, providers_to_df, patients_to_df, process_appointments
from src.scripts.salesforce_transformer import *
from src.utils.salesforce_functions import load_data_to_salesforce_rest
from src.utils.salesforce_mapper import build_sf_id_maps
from simple_salesforce import Salesforce
import os


def run_pipeline():
    # 2. Setup - Connections and environment variables
    ehr = EHR()
    sf = Salesforce(...)
    organization_id = os.getenv('HAPI_ORG_ID')
    print("ETL Pipeline Initialized...")

    # 3. EXTRACT - Get data from the source EHR
    print("\n--- Starting EXTRACT Phase ---")
    locations_df = locations_to_df(ehr, organization_id)
    providers_df = providers_to_df(ehr, organization_id)
    patients_df = patients_to_df(ehr, organization_id)
    appointments_df = process_appointments(ehr, organization_id)
    print("✅ Extract phase complete.")

    # 4. TRANSFORM - Prepare data for Salesforce
    print("\n--- Starting TRANSFORM Phase ---")
    sf_territories_df = transform_locations_for_sf(locations_df)
    sf_work_types_df = transform_work_types_for_sf()
    sf_users_df = transform_users_for_sf(providers_df)
    sf_patients_df = transform_patients_for_sf(patients_df)
    # Note: Some transformations depend on data loaded into Salesforce (e.g., User IDs for Service Resources)
    print("✅ Initial transform phase complete.")

    # 5. LOAD (Part 1) - Load independent objects
    print("\n--- Starting LOAD Phase (Part 1) ---")
    location_results = load_data_to_salesforce_rest(sf, sf_territories_df, 'ServiceTerritory')
    user_results = load_data_to_salesforce_rest(sf, sf_users_df, 'User')
    patient_results = load_data_to_salesforce_rest(sf, sf_patients_df, 'Account')
    work_types_results = load_data_to_salesforce_rest(sf, sf_work_types_df, 'WorkType')

    # 6. MAP - Get Salesforce IDs for dependent objects
    print("\n--- Starting MAP Phase ---")
    # This map now includes the User IDs we just loaded
    user_id_map = {rec['original_data']['Email']: rec['sf_id'] for rec in user_results['successful_records']}
    
    # 7. TRANSFORM (Part 2) - Transform dependent objects
    print("\n--- Starting TRANSFORM Phase (Part 2) ---")
    sf_sresources_df = transform_sresources_for_sf(providers_df, user_id_map)

    # 8. LOAD (Part 2) - Load dependent objects
    print("\n--- Starting LOAD Phase (Part 2) ---")
    sresources_results = load_data_to_salesforce_rest(sf, sf_sresources_df, 'ServiceResource')

    # 9. Final Mapping & Loading for Appointments
    sf_id_maps = build_sf_id_maps(sf) # Now this will get ALL the required IDs
    sf_appointments_df = transform_appointments_for_sf(appointments_df, sf_id_maps)
    appointment_results = load_data_to_salesforce_rest(sf, sf_appointments_df, 'ServiceAppointment')
    
    print("\n🎉 ETL Pipeline Finished Successfully! 🎉")

if __name__ == '__main__':
    run_pipeline()