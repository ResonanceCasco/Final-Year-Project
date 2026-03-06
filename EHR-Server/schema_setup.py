#!/usr/bin/env python3
"""
EHR Database Schema Setup
Creates PostgreSQL tables for healthcare data
"""
import psycopg2
form psycopg2 import sql
import sys

# Database configuration
DB_CONFIG = {
    'dbname': 'healthcare'
    'user': 'ehr_admin',
    'password': 'SecurePass2024!'
    'host': 'localhost', # Will be DATA VLAN IP when deployed
    'port': 5432
}

def create_connection():
    """Create database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("Connected to PostgreSQL database")
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        sys.exit(1)

def create_patients_table(cursor):
    """Create patients table"""
    query = """
    CREATE TABLE IF NOT EXISTS patients (
        patient_id VARCHAR(50) PRIMARY KEY,
        first_name VARCHAR(100) NOT NULL,
        last_name VARCHAR(100) NOT NULL,
        date_of_birth DATE NOT NULL,
        gender VARCHAR(20),
        pps VARCHAR(9),
        address TEXT,
        city VARCHAR(100),
        state VARCHAR(50),
        eircode VARCHAR(8),
        phone VARCHAR(20),
        email VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    cursor.execute(query)
    print("Created patients table")

def create_encounters_table(cursor):
    """Create medical encounters table"""
    query = """
    CREATE TABLE IF NOT EXISTS encounters (
        encounter_id VARCHAR(50) PRIMARY KEY,
        patient_id VARCHAR(50) NOT NULL,
        encounter_date TIMESTAMP NOT NULL,
        encounter_type VARCHR(100),
        reason_code VARCHAR(50),
        reason_description TEXT,
        provider_name VARCHAR(200),
        facility VARCHAR(200),
        cost DECIMAL(10, 2),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE
    );
    """
    cursor.execute(query)
    print("Created encounters table")

def create_conditions_table(cursor):
    """Create conditions/diagnses table"""
    query = """
    CREATE TABLE IF NOT EXISTS conditions (
        condtion_id SERIAL PRIMARY KEY,
        patient_id VARCHAR(50) NOT NULL,
        encounter_id VARCHAR(50),
        onset_date DATE,
        resolved_date DATE,
        condition_code VARCHAR(50),
        conditioon_description TEXT NOT NULL,
        severity VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
        FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id) ON DELETE SET NULL
    );
    """
    cursor.execute(query)
    print("Created conditions table")

def create_medications_table(cursor):
    """Create medications table"""
    query = """
    CREATE TABLE IF NOT EXISTS medications (
        medication_id SERIAL PRIMARY KEY,
        patient_id VARCHAR(50) NOT NULL,
        encounter_id VARCHAR(50),
        medication_code VARCHAR(50),
        medication_name TEXT NOT NULL,
        dosage VARCHAR(100),
        start_date DATE,
        end_date DATE,
        prescriber VARCHAR(200),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
        FOREIGN KEY (encounter_id) REFERENCES patients(patient_id) ON DELETE SET NULL
    );
    """    
    cursor.execute(query)
    print("Created medications table")

def create_observations_table(cursor):
    """Create observations/vitals table"""
    query = """
    CREATE TABLE IF NOT EXISTS observations (
        observation_id SERIAL PRIMARY KEY,
        patient_id VARCHAR(50) NOT NULL,
        encounter_id VARCHAR(50),
        observation_date TIMESTAMP NOT NULL,
        observation_type VARCHAR(100) NOT NULL,
        observation_code VARCHAR(50),
        value VARCHAR(50),
        unit VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
        FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id) ON DELETE SET NULL
    );
    """
    cursor.execute(query)
    print("Created obseravtions table")

def create_allergies_table(cursor):
    """Create allergies table"""
    query = """
    CREATE TABLE IF NOT EXISTS allergies (
        allergy_id SERIAL PRIMARY KEY,
        patient_id VARCHAR(50) NOT NULL,
        allergen VARCHAR(200) NOT NULL,
        allergy_type VARCHAR(50),
        severity VARCHAR(50),
        reaction TEXT,
        onset_date DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE
    );
    """
    cursor.execute(query)
    print("Created allergies table")

def create_procedures_table(cursor):
    """Create procedures table"""
    query = """
    CREATE TABLE IF NOT EXISTS procedures (
        procedure_id SERIAL PRIMARY KEY,
        patient_id VARCHAR(50) NOT NULL,
        encounter_id VARCHAR(50),
        procedure_date DATE NO NULL,
        procedure_code VARCHAR(50),
        procedure_description TEXT NOT NULL,
        performer VARCHAR(200),
        cost DECIMAL(10, 2),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
        FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id) ON DELETE SET NULL
    );
    """
    cursor.execute(query)
    print("Created procedures table")

def create_access_log_table(cursor):
    """Create access audit log table"""
    query = """
    CREATE TABLE IF NOT EXISTS access_logs (
        log_id SERIAL PRIMARY KEY,
        user_id VARCHAR(100) NOT NULL,
        patient_id  VARCHAR(50),
        access_type VARCHAR(50) NOT NULL,
        access_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        source_ip VARCHAR(50),
        action VARCHAR(100),
        success BOOLEAN DEFAULT TRUE,
        blockchain_tx_hash VARCHAR(100)
    );
    """
    cursor.execute(query)
    print("Created access_logs table")

def create_indexes(cursor):
    """Create indexes for better query peformance"""
    indexes = []
