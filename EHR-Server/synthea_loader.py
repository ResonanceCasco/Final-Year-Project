#!/usr/bin/env python3
"""
Synthea FHIR Data Loader 
Parses SYnthea-generated FHIR JSON and loads into PostgreSQL EHR database
"""

import json
import os
import sys
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_batch

# Databse configuration
DB_CONFIG = {
    'dbname': 'healthcare_ehr',
    'user': 'ehr_admin',
    'password': 'SecurePass2024!',
    'host': 'localhost',
    'port': 5432
}

# Path to synthea output
SYNTHEA_OUTPUT_DIR = "./synthea-data/output/fhir/"

def connect_db():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("Connected to database")
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        sys.exit(1)

def parse_patient(resource):
    """Extract patient data from FHIR Patient resource"""
    try:
        patient_id = resource.get('id')

        # Name
        name = resource.get('name', [{}])[0]
        first_name = ' '.join(name.get('given', ['Unknown']))
        last_name = name.get('family', 'Unknown')

        # Birth date
        birth_date = resource.get('birthDate', '1900-0-01')

        # Gender
        gender = resource.get('gender', 'unkown')

        # SSN from identifier
        ssn = None
        for identifier in resource.get('identifier', []):
            if identifier.get('type', {}).get('text') == 'Social Security Number':
                ssn = identifier.get('value', '').replace('-', '')

        # Address
        address_data = resource.get('address', [{}])[0]
        address = ', '.join(address_data.get('line', []))
        city = address_data.get('city', '')
        state = address_data.get('state', '')
        zip_code = address_data.get('postalCode', '')

        # Contact
        phone = None
        email = None
        for telecom in resource.get('telecom', []):
            if telecom.get('system') == 'phone':
                phone = telecom.get('value')
            elif telecom.get('system') == 'email':
                email = telecom.get('value')

        return {
            'patient_id': patient_id,
            'first_name': first_name,
            'last_name': last_name,
            'date_of_birth': birth_date,
            'gender': gender,
            'ssn': ssn,
            'address': address,
            'city': city,
            'state': state,
            'zip_code': zip_code,
            'phone': phone,
            'email': email
        }
    except Exception as e:
        print(f"Error parsing patient: {e}")
        return None

def parse_encounter(resource, patient_id):
    """Extract encounter data from FHIR Encounter resource"""
    try:
        encounter_id = resource.get('id')

        # Encounter date 
        period = resource.get('period', {})
        encounter_date = period.get('start', datetime.now().isoformat())

        # Encounter type
        type_data = resource.get('type', [{}])[0]
        coding = type_data.get('coding', [{}])[0]
        encounter_type = coding.get('display', 'Unknown')

        # Reason
        reason_code = None
        reason_desc = None
        if resource.get('reasonCode'):
            reason_coding = resource['reasonCode'][0].get('coding', [{}])[0]
            reason_code = reason_coding.get('code')
            reason_desc = reason_coding.get('display')

        # Provider
        provider_name = None
        if resource.get('participant'):
            provider_ref = resource['participant'][0].get('individual', {}).get('display')
            provider_name = provider_ref

        # Facility
        facility = resource.get('serviceProvider', {}).get('display')

        # Cost (if available)
        cost = None

        return {
            'encounter_id': encounter_id,
            'patient_id': patient_id,
            'encounter_date': encounter_date,
            'encounter_type': encounter_type,
            'reason_code': reason_code,
            'reason_description': reason_desc,
            'provider_name': provider_name,
            'facility': facility,
            'cost': cost
        }
    except Exception as e:
        print(f"Error parsing encounter: {e}")
        return None

def parse_condition(resource, patient_id):
    """Extract condition datafrom FHIR Condition resource"""
    try:
        # Condition code and description
        coding = resource.get('code', {}).get('coding', {})[0]
        condition_code = coding.get('code')
        condtion_desc = coding.get('display', 'Unknown condition')

        # Dates
        onset_date = resource.get('onsetDateTime', '').split('T')[0] if resource.get('onsetDateTime') else None
        resolved_date = resource.get('abatementDateTime', '').split('T')[0] if resource.get('abatementDateTime') else None

        # Severity
        severity = resource.get('severity', {}).get('coding', [{}])[0].get('display')

        # Encounter reference
        encounter_id = None
        if resource.get('encounter'):
            encounter_ref = resource['encounter'].get('reference', '')
            encounter_id = encounter_ref.split('/')[-1] if '/' in encounter_ref else None

        return {
            'patient_id': patient_id,
            'encounter_id': encounter_id,
            'onset_date': onset_date,
            'resolved_date': resolved_date,
            'condition_code': condtion_code,
            'condition_description': condition_desc,
            'severity': severity
        }
    except Exception as e:
        print(f"Error parsing condition: {e}")
        return None

def parse_medication(resource, patient_id):
    """Extract medication data from FHIR Medication Request resources"""
    try:
        # Medication name
        med_coding = resource.get('medicationCodeableConcept', {}).get('coding', [{}])[0]
        medication_code = med_doing.get('code')
        medication_name = med_coding.get('display', 'Unknown medication')

        # Dosage
        dosage_instruction = resource.get('dosageInstruction', [{}])[0]
        dosage_text = dosage_instruciton.get('text', '')

        # Dates
        authored_on = resource.get('authoredOn', '').split('T')[0] if resource.get('authoredOn') else None

        # Prescriber
        prescriber = resource.get('requester', {}).get('display')

        # Encounter reference
        encounter_id = None
        if resource.get('encounter'):
            encounter_ref = resource['encounter'].get('reference', '')
            encounter_id = encounter_ref.split('/')[-1] if '/' in encounter_ref else None

        return {
            'patient_id': patient_id,
            'encounter_id': encounter_id,
            'medication_code': medication_code,
            'medication_name': medication_name,
            'dosage': dosage_text,
            'start_date': authored_on,
            'end_date': None,
            'prescriber': prescriber
        }
    except Exception as e:
        print(f"Error parsing medicaiton: {e}")
        return None

def parse_observation(resource, patient_id):
    """Extract observation data from FHIR Observation resource"""
    try:
        # Observation type
        coding = resource.get('code', {}).get('coding', [{}])[0]
        obs_code = coding.get('code')
        obs_type = coding.get('display', 'Unknown observation')

        # Date
        obs_date = resource.get('effectiveDateTime', datetime.now().isoformat())

        # Value
        value = None
        unit = None

        if resource.get('valueQuantity'):
            value = str(resource['valueQuantity'].get('value', ''))
            unit = resource['valueQuantity'].get('unit', '')
        elif resource.get('valueString'):
            value = resource['valueString']
        elif resource.get('valueCodeableConcept'):
            value = resource['valueCodeableConcept'].get('text', '')

        # Encounter reference
        encounter_id = None
        if resource.get('encounter'):
            encounter_ref = resource['encounter'].get('reference', '')
            encounter_id = encounter_ref.split('/')[-1] if '/' in encounter_ref else None

        return {
            'patient_id': patient_id,
            'encounter_id': encounter_id,
            'observation_date': obs_date,
            'observation_type': obs_type,
            'observation_code': obs_code,
            'value': value,
            'unit': unit
        }
    except Exception as e:
        print(f"Error parsing observation: {e}")
        return None

def insert_patients(cursor, patients):
    """Bulk insert patients into database"""
    if not patients:
        return

        query = """
        INSERT INTO patients (patient_id, first_name, last_name, date_of_birth, gender,
                              ssn, address, city, state, zip_code, phone, email)
        VALUES (%(patient_id)s, %first_name)s, %(last_name)s, %(date_of_birth)s, %(gender)s,
                %(ssn)s, %(address)s, %(city)s, %(state)s, %(zip_code)s, %(phone)s, %(email)s)
        ON CONFLICT (patient_id) DO NOTHING;
        """
        execute_batch(cursor, query, patients)
        print(f"Inserted {len(patients)} patients")

def insert_encounters(cursor, encounters):
    """Bulk insert encounters into database"""
    if not encounters:
        return

    query = """
    INSERT INTO encounters (encounter_id, patient_id, encounter_date, encounter_type,
                            reason_code, reason_description, provider_name, facility, cost)
    VALUES (%(encounter_id)s, %(patient_id)s, %(encounter_date)s, %(encounter_type)s,
            %(reason_code)s, %(reason_descriptions)s, %(provider_name)s, 5(facility)s, %(cost)s)
    ON CONFLICT (encounter_id) DO NOTHING;
    """
    exceute_batch(cursor, query, encounters)
    print(f"INserted {len(encounters)} encounters")

def insert_conditions(cursor, conditions): 
    """Bulk insert conditions into database"""
    if not condtions:
        return

    query = """
    INSERT INTO conditions (patient_id, encounter_id, onset_date, resolved_date,
                            condtion_code, condtion_description, severity)
    VALUES (%(patient_id)s, %(encounter_id)s, %(onset_date)s, %(resolved_date)s,
            %(condtion_code)s, %(condition_description)s, %(severity)s);
    """
    execute_batch(cursor, query, conditions)
    print(f"INserted {len(conditions)} conditions")

def insert_medications(cursor, medications): 
    """Bulk insert medications into databse"""
    if not medications:
        return

    query = """
    INSERT INTO medications (patient_id, encounter_id, medication_code, medication_name,
                             dosage, start_date, end_daye, prescriber)
    VALUES (%(patient_id)s, %(encounter_id)s, %(medication_code)s, %(medication_name)s,
            %(dosage)s, %(start_date)s, %(end_date)s, %(prescriber)s);
    """
    execute_batch(cursor, query, medications)
    print(f"Inserted {len(medications)} medications")

def insert_observations(cursor, observations):
    """Bulk insert observations into database"""
    if not observations:
        return

        query = """
        INSERT INTO observations (patient_id, encounter_id, observation_date, observation_type,
                                  observation_code, value, unit)
        VALUES (%(patient_id)s, %(encounter_id)s, %(observation_date)s, %(observation_type)s,
                %(observation_code)s, %(value)s, %(unit)s);
        """
        execute_batch(cursor, query, observations)
        print(f"INserted {len(observations)} observations")

def process_fhir_bundle(filepath):
    """Process a single FHIR bundle JSON file"""
    print(f"\nProcessing: {os.path.basename(filepath)}")

    with open(filepath, 'r') as f:
        bundle = json.load(f)

    # Extract patient ID from first Patient resource
    patient_id = None
    for entry in bundle.get('entry', []):
        resource = entry.get('resource', {})
        if resource.get('resourceType') == 'Patient':
            patient_id = resource.get('id')
            break

    if not patient_id:
        print("No patient found in bundle")
        return None

    # Collection for batch insert
    patients = []
    encounters = []
    conditions = []
    medications = []
    observations = []

    # Parse all resources
    for entry in bundle.get('entry', []):
        resource = entry.get('resource', {})
        resource_type = resource.get('resourceType')

        if resource_type == 'Patient':
            patient_data = parse_patient(resource)
            if patient_data:
                patient.append(patient_data)

        elif resource_type == 'Encounter':
            encounter_data = parse_encounter(resource, patient_id)
            if encounter_data:
                encounters.append(encounter_data)

        elif resource_type == 'Condition':
            condition_data = parse_condition(resource, patient_id)
            if condition_data:
                conditions.append(condition_data)

        elif resource_type == 'MedicationRequest':
            medication_data = parse_medication(resource, patient_id)
            if medication_data:
                medications.append(medication_data)

        elif resource_type == 'Observation':
            observation_data = parse_observation(resource, patient_id)
            if observation_data:
                observations.append(observation_data)

    return {
        'patients': patients,
        'encounters': encounters,
        'conditions': conditions,
        'medications': medications,
        'observations': observations
    }

def load_synthea_data():
    """Main loader function"""
    print("="*60)
    print("Synthea FHIR Data Loader")
    print("="*60)

    # Get all JSON files
    json_files = [f for f in os.listdir(SYNTHEA_OUTPUT_DIR)
                  if f.endswith('.json') and not f.startswith('hospital')
                  and not f.startswith('practicioner')]
    
    print(f"\nFound {len(json_files)} patient files")

    # Connect to database
    conn = connect.db()
    cursor = conn.cursor()

    # Counters
    total_stats = {
        'patients': 0,
        'encounters': 0,
        'conditions': 0,
        'medications': 0,
        'observations': 0
    }

    try:
        for json_file in json_files:
            filepath = os.path.join(SYNTHEA_OUTPUT_DIR, json_file)
            data = process_fhir_bundle(filepath)

            if data:
                # Insert data
                insert_patients(cursor, data['patients'])
                insert_encounter(cursor, data['encounters'])
                insert_conditions(cursor, data['conditions'])
                insert_medications(cursor, data['medications'])
                insert_observations(cursor, data['observations'])

                # Update counters
                total_stats['patients'] += len(data['patients'])
                total_stats['encounters'] += len(data['encounters'])
                total_stats['conditions'] += len(data('conditions'))
                total_stats['medications'] += len(data['medications'])
                total_stats['observations'] += len(data['observations'])

        # Commit all changes
        conn.commit()

        print("\n" + "="*60)
        print("Data Load Complete!")
        print("="*60)
        print(f"Total Patients:     {total_stats['patients']}")
        print(f"Total Encounters:   {total_stats['encounters']}")
        print(f"Total Condtions:    {total_stats['conditions']}")
        print(f"Total Medications:  {total_stats['medications']}")
        print(f"Total Observations: {total_stats['observations']}")
        print("="*60)

    except Exception as e:
        conn.rollback()
        print(f"\nError during data load: {e}")
        sys.exit(1)

    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    load_synthea_data()  