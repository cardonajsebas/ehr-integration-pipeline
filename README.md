# EHR to Salesforce ETL Pipeline

A Python ETL pipeline that integrates FHIR-compliant Electronic Health Record data with Salesforce Health Cloud. Extracts patient, provider, and appointment data from a public HAPI FHIR API, transforms it with Pandas, and loads it into the corresponding Salesforce Health Cloud objects.

> Built as a portfolio project to demonstrate data engineering skills in healthcare API integration, ETL pipeline design, and Salesforce data loading.

---

## Context

Healthcare systems store clinical data in FHIR (Fast Healthcare Interoperability Resources) format, an industry standard for exchanging health information. This pipeline bridges that format with Salesforce Health Cloud, which uses its own relational object model. The transformation layer handles the structural mismatch between hierarchical FHIR JSON and the flat, ID-linked Salesforce schema.

The pipeline uses the public [HAPI FHIR server](https://hapi.fhir.org/) as the source system, making it fully reproducible without access to a real EHR system.

---

## Architecture

```
ehr-integration-pipeline/
│
├── src/
│   ├── api/
│   │   └── ehr_client.py               # HAPI FHIR API client
│   ├── pipelines/
│   │   └── main_etl_pipeline.py        # Pipeline orchestrator
│   ├── scripts/
│   │   ├── ehr_data_loader.py          # Seeds the FHIR server with mock data
│   │   ├── ehr_data_processor.py       # Extracts and parses FHIR resources
│   │   └── salesforce_transformer.py   # Transforms FHIR data to Salesforce schema
│   └── utils/
│       ├── mock_data.py                # Mock patient and appointment data
│       ├── salesforce_functions.py     # Generic Salesforce loading functions
│       └── salesforce_mapper.py        # Maps existing Salesforce IDs
│
├── tests/                              # Unit tests
├── requirements.txt
├── .env.example
└── README.md
```

---

## ETL Flow

| Stage | Script | Description |
|---|---|---|
| Extract | `ehr_data_processor.py` | Pulls Locations, Practitioners, Patients, and Appointments from HAPI FHIR |
| Transform | `salesforce_transformer.py` | Reshapes FHIR JSON into Salesforce-compatible flat records |
| Load | `salesforce_functions.py` | Inserts records into Salesforce objects in dependency order |

**Salesforce objects loaded:**

| FHIR Resource | Salesforce Object |
|---|---|
| Location | ServiceTerritory |
| Practitioner | User, ServiceResource |
| Patient | Account |
| Appointment | WorkType, ServiceAppointment |

Load order follows object dependencies: `User` records are created before their associated `ServiceResource` records.

---

## Tech Stack

| Tool | Purpose |
|---|---|
| **Python** | Core ETL scripting |
| **Pandas** | Data transformation and reshaping |
| **HAPI FHIR API** | Source EHR system (public FHIR R4 server) |
| **Simple Salesforce** | Salesforce REST API client |
| **Salesforce Health Cloud** | Target system for transformed data |

---

## Prerequisites

- Python 3.9+
- A Salesforce Developer Edition org with Health Cloud installed
- Access to the public HAPI FHIR server (no credentials required)

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/cardonajsebas/ehr-integration-pipeline
cd ehr-integration-pipeline
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your credentials:

```bash
# Salesforce credentials
SF_USERNAME=your_salesforce_username@example.com
SF_PASSWORD=your_salesforce_password
SF_SECURITY_TOKEN=your_salesforce_security_token

# HAPI FHIR organization ID
HAPI_ORG_ID=your_hapi_org_id
```

The `HAPI_ORG_ID` is created by the seed script in Step 1 of the pipeline below.

---

## How to Run

### Step 1 - Seed the EHR with mock data

Creates `Organization`, `Location`, `Practitioner`, `Patient`, and `Appointment` records on the public HAPI FHIR server. Skip this step if you already have an existing organization ID with data.

```bash
python -m src.scripts.ehr_data_loader
```

Copy the generated `HAPI_ORG_ID` from the output and add it to your `.env` file.

### Step 2 - Run the ETL pipeline

Executes the full Extract, Transform, and Load process. Progress and load results are printed to the console.

```bash
python -m src.pipelines.main_etl_pipeline
```

---

## Credits

Built using the [HAPI FHIR public test server](https://hapi.fhir.org/) and the [Simple Salesforce](https://github.com/simple-salesforce/simple-salesforce) library.

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## About

Built by **John S Cardona** as a portfolio project demonstrating data engineering skills in API integration and ETL pipeline design.

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/sebastian-cardona)
[![Portfolio](https://img.shields.io/badge/Portfolio-000000?style=for-the-badge&logo=google-chrome&logoColor=white)](https://cardonajsebas.github.io/)
[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/cardonajsebas)