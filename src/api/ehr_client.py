import requests
import time


class EHR:
    """
    Base class for Electronic Health Record (EHR) integrations.
    Provides common functionality for creating and geting FHIR resources.
    """

    def __init__(self, base_url="https://hapi.fhir.org/baseR4"):
        self.base_url = base_url
        self.headers = {'Content-Type': 'application/fhir+json'}


# Database and main record types creation

    def _post_resource(self, resource_type:str, payload:dict) -> dict:
        """
        Internal helper to POST any FHIR resource.

        Args:
            resource_type (str): e.g. 'Organization', 'Location', 'Practitioner'
            payload (dict): JSON payload for the resource

        Returns:
            dict: API response JSON
        """
        response = requests.post(
            f'{self.base_url}/{resource_type}',
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()

    # Organization
    def post_organization(self, new_org:dict) -> dict:
        """Create a new Organization resource."""
        return self._post_resource('Organization', new_org)

    # Location
    def post_location(self, new_location:dict) -> dict:
        """Create a new Location resource."""
        return self._post_resource('Location', new_location)

    # Practitioner
    def post_practitioner(self, new_practitioner:dict) -> dict:
        """Create a new Practitioner resource."""
        return self._post_resource('Practitioner', new_practitioner)

    # Practitioner Role
    def post_practitioner_role(self, new_pract_role:dict) -> dict:
        """Create a new PractitionerRole resource."""
        return self._post_resource('PractitionerRole', new_pract_role)

    # Patient
    def post_patient(self, patient:dict) -> dict:
        """
        Create a new Patient resource in the FHIR server.

        Args:
            patient (dict): JSON payload for the Patient resource

        Returns:
            dict: API response JSON
        """
        return self._post_resource('Patient', patient)

    # Appointment
    def post_appointment(self, appointment:dict) -> dict:
        """
        Create a new Appointment resource in the FHIR server.

        Args:
            appointment (dict): JSON payload for the Appointment resource

        Returns:
            dict: API response JSON
        """
        return self._post_resource('Appointment', appointment)


    # Data collection

    # Main functions:
    def get_resource(self, resource_type:str, search_criteria:str) -> dict:
        """
        Get a resource from HAPI FHIR public server.

        Args:
            resource_type (str): e.g. 'Patient', 'Practitioner', 'Appointment'
            search_criteria (str): Search criteria field and its value
        
        Returns:
            dict: JSON response
        """
        url = f"{self.base_url}/{resource_type}/_search?{search_criteria}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def get_all_resources(self, url:str, params:dict = None) -> list:
        """
        Get all resources from a paginated HAPI FHIR endpoint.

        Args:
            url (str): Base resource URL (e.g., f"{BASE_URL}/Appointment").
            params (dict): Query params (e.g., {'actor': 'Practitioner/123'}).

        Returns:
            list: Combined list of all resource entries across pages.
        """
        entries = []
        while url:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            entries.extend(data.get('entry', []))
            # look for 'next' link in bundle
            url = None
            for link in data.get('link', []):
                if link.get('relation') == 'next':
                    url = link.get('url')
                    params = None
                    break
        return entries

    # Practitioners:
    def get_practitioner_roles(self, org_id:str, count:int = 50) -> dict:
        """
        Fetch PractitionerRole resources for a given Organization.
        """
        url = f'{self.base_url}/PractitionerRole'
        params = {
            '_count': count,
            'organization': f'Organization/{org_id}'
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_practitioner(self, practitioner_id:str) -> dict:

        """
        Fetch a single Practitioner resource by ID.
        """
        url = f'{self.base_url}/Practitioner/{practitioner_id}'
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

# Appointments:
    def get_all_appointments(self, organization_id: str) -> list:
        """
        Fetch all Appointment resources linked to an Organization (handles pagination).

        Args:
            organization_id (str): The ID of the managing Organization.

        Returns:
            list: A list of all appointment "entry" objects from the FHIR bundle.
        """
        url = f"{self.base_url}/Appointment"
        
        params = {"patient.organization": f"Organization/{organization_id}"}
        
        entries = self.get_all_resources(url, params)
        return entries


