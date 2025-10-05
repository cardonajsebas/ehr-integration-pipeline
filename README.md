# EHR to Salesforce ETL Pipeline

## Abstract
This project is a demonstration of a complete **ETL (Extract, Transform, Load)** pipeline built with **Python**. It simulates a real-world data engineering task: integrating a healthcare provider's **Electronic Health Record (EHR)** system with **Salesforce Health Cloud**.

The pipeline extracts patient, provider, and appointment data from a public **FHIR-compliant API (HAPI FHIR)**, transforms the data into a schema compatible with Salesforce objects, and loads it into a Salesforce Developer Org.

**Core Technologies**: Python, Pandas, HAPI FHIR API, Simple Salesforce, Salesforce REST API.

## Features

### Modular ETL Architecture
The code is cleanly separated into distinct **Extract**, **Transform**, and **Load** stages for clarity and maintainability.

### EHR Data Extraction
Connects to a FHIR API to pull key healthcare resources:
* Locations
* Practitioners & Practitioner Roles
* Patients
* Appointments

### Data Transformation
Utilizes the **Pandas** library to clean, reshape, and map the hierarchical JSON data from the EHR into relational tables ready for Salesforce.

### Salesforce Data Loading
Inserts the transformed data into the corresponding Salesforce Health Cloud objects:
* `ServiceTerritory` (from Locations)
* `User` & `ServiceResource` (from Practitioners)
* `Account` (from Patients)
* `WorkType`
* `ServiceAppointment` (from Appointments)

### Dependency Handling
The pipeline correctly loads objects in the required order, handling dependencies such as creating `User` records before their associated `ServiceResource` records.

### Environment Configuration
Securely manages credentials and environment-specific IDs using a `.env` file.

### Data Seeding
Includes a script to populate the source EHR system with mock data, making the project fully reproducible.

---
## Project Architecture
The project follows a logical and scalable structure that separates concerns:

    └───ehr_etl_project
        ├───main.py                 # Main entry point to run the pipeline
        ├───.env                    # For storing environment variables (credentials, IDs)
        ├───README.md               # This file
        ├───requirements.txt        # Project dependencies
        │
        └───src
            ├───api                 # API client for the EHR system
            │   └───ehr_client.py
            ├───pipelines           # High-level orchestrators for ETL jobs
            │   └───main_etl_pipeline.py
            ├───scripts             # Individual, runnable scripts
            │   ├───ehr_data_loader.py      # Seeds the source EHR with mock data
            │   ├───ehr_data_processor.py   # Extracts and parses data from the EHR
            │   └───salesforce_transformer.py # All data transformation logic
            └───utils               # Reusable utility functions
                ├───mock_data.py
                ├───salesforce_functions.py # Generic Salesforce data loading functions
                └───salesforce_mapper.py    # Queries Salesforce to map existing IDs

---

## Setup and Installation

### Prerequisites:
* **Python 3.9+**
* A **Salesforce Developer Edition Org** preferibly with the Health Cloud package installed.

Follow these steps to set up the project locally:

1.  **Clone the repository**:
    ```bash
    git clone <your-repository-url>
    cd ehr_etl_project
    ```

2.  **Create and activate a virtual environment**:
    ```bash
    # For Windows
    python -m venv venv
    .\venv\Scripts\activate

    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install the required dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables**:
    Create a file named `.env` in the root directory of the project and populate it with your credentials. **This file should not be committed to version control.**

    ```ini
    # .env file
    # Salesforce Credentials
    SF_USERNAME="your_salesforce_username@example.com"
    SF_PASSWORD="your_salesforce_password"
    SF_SECURITY_TOKEN="your_salesforce_security_token"

    # HAPI FHIR Organization ID (can be pre-generated or created by the loader script)
    HAPI_ORG_ID="your_hapi_org_id"
    ```
---

## How to Run the Pipeline
The pipeline is a two-step process. First, you seed the source EHR with mock data. Second, you run the ETL pipeline to move that data to Salesforce.

### Step 1: Seed the EHR with Mock Data
This script creates the necessary `Organization`, `Location`, `Practitioner`, `Patient`, and `Appointment` records in the public HAPI FHIR server.

```bash
python -m src.scripts.ehr_data_loader
```
(Note: This step can be skipped if you are targeting an existing organization ID in the .env file that already has data.)

Step 2: Run the Main ETL Pipeline
This script executes the full Extract, Transform, and Load process.
```bash
python -m src.pipelines.main_etl_pipeline
```

The script will print its progress to the console, showing the status of each phase and summarizing the results of the data loads into Salesforce.