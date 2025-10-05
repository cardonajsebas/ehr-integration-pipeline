import pandas as pd
import random
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()


# Constants
AREA_CODES = ['305', '786']
EMAIL_DOMAINS = ['@gmail.com.invalid','@outlook.com.invalid','@aol.com.invalid','@yahoo.com.invalid']
CITIES = ['Miami', 'Hialeah', 'Coral Gables', 'Miami Beach']
ZIPCODES = ['33127','33137','33140','33130','33150','33156','33126','33183','33186','33193']
TODAY = datetime(2025, 9, 26)
PAST_STATUSES = ['fulfilled', 'cancelled']
FUTURE_STATUSES = ['booked', 'cancelled']

# Patients
def generate_patient_data(n: int, organization_id: str) -> pd.DataFrame:
    """Generate mock patient data for Miami-Dade area."""
    patients = []
    for _ in range(n):
        gender = random.choice(['male', 'female'])
        first_name = fake.first_name_male() if gender == 'male' else fake.first_name_female()
        last_name = fake.last_name()
        birth_date = fake.date_of_birth(minimum_age=18, maximum_age=90).isoformat()

        phone = random.choice(AREA_CODES)+ f'-{random.randint(200,999)}-{random.randint(1000,9999)}'
        email = f'{first_name.lower()}.{last_name.lower()}' + random.choice(EMAIL_DOMAINS)

        address = {
            'line': [fake.street_address()],
            'city': random.choice(CITIES),
            'state': 'FL',
            'postalCode': random.choice(ZIPCODES)
        }

        patients.append({
            'first_name': first_name,
            'last_name': last_name,
            'birthDate': birth_date,
            'gender': gender,
            'phone': phone,
            'email': email,
            'address': address,
            'organization_id': organization_id
        })

    return pd.DataFrame(patients)

# Appointments
def random_weekday(start_date: datetime, end_date: datetime) -> datetime:
    """Pick a random weekday datetime between start_date and end_date."""
    while True:
        dt = start_date + timedelta(
            days=random.randint(0, (end_date - start_date).days),
            hours=random.randint(8, 16),
            minutes=random.choice([0, 15, 30, 45])
        )
        if dt.weekday() < 5:  # Mon–Fri only
            return dt

def make_appointment_dict(row, work_types: dict) -> dict:
    """
    Build a FHIR Appointment resource dictionary from a row in the appointments DataFrame.

    Args:
        row (pd.Series): Row from appointments DataFrame
        work_types (dict): Dictionary of work types with system, code, display

    Returns:
        dict: Appointment resource JSON
    """
    wk = next((v for v in work_types.values() if v['display'] == row['work_type']), None)
    if not wk:
        raise ValueError(f"Invalid work_type: {row['work_type']}")

    return {
        'resourceType': 'Appointment',
        'status': row['status'],
        'serviceType': [
            {
                'coding': [
                    {
                        'system': wk['system'],
                        'code': wk['code'],
                        'display': wk['display'],
                    }
                ],
                'text': wk['display'],
            }
        ],
        'start': row['start'].strftime('%Y-%m-%dT%H:%M:%SZ'),
        'end': row['end'].strftime('%Y-%m-%dT%H:%M:%SZ'),
        'participant': [
            {'actor': {'reference': f"Patient/{row['patient_id']}"}, 'status': 'accepted'},
            {'actor': {'reference': f"Practitioner/{row['provider_id']}"}, 'status': 'accepted'},
            {'actor': {'reference': f"Location/{row['location_id']}"}, 'status': 'accepted'},
        ],
    }

def generate_appointments(
    patients_df: pd.DataFrame,
    providers_df: pd.DataFrame,
    locations_df: pd.DataFrame,
    work_types: dict,
    n: int = 500) -> pd.DataFrame:
    """
    Generate random appointments DataFrame using available patients, providers, locations, and work types.

    Args:
        patients_df (pd.DataFrame): Must include 'patient_id'
        providers_df (pd.DataFrame): Must include 'practitioner_id'
        locations_df (pd.DataFrame): Must include 'location_id'
        work_types (dict): Dictionary of work types
        n (int): Number of appointments to generate

    Returns:
        pd.DataFrame: Appointments with columns
            [patient_id, provider_id, location_id, work_type, start, end, status]
    """
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2026, 6, 30)

    records = []
    for _ in range(n):
        patient = random.choice(patients_df['patient_id'].tolist())
        provider = random.choice(providers_df['practitioner_id'].tolist())
        location = random.choice(locations_df['location_id'].tolist())
        work_key, work = random.choice(list(work_types.items()))
        start_dt = random_weekday(start_date, end_date)
        end_dt = start_dt + timedelta(minutes=random.choice([15, 30, 45, 60]))

        if start_dt < TODAY:
            status = random.choice(PAST_STATUSES)
        else:
            status = random.choice(FUTURE_STATUSES)

        records.append({
            'patient_id': patient,
            'provider_id': provider,
            'location_id': location,
            'work_type': work['display'],
            'start': start_dt,
            'end': end_dt,
            'status': status
        })

    return pd.DataFrame(records)


