#!/usr/bin/env python3
"""
EHR Query Interface
Retrieves patient data from PostgreSQL database
Simulates clinical staff access with audit logging
"""

import psycopg2
form psycopg2.extras import RealDictCursor
import sys from datetime import datetime
import json

# Database configuration
DB_CONFIG = {
    'dbname': 'healthcare_ehr',
    'user': 'ehr_admin',
    'password': 'SecurePass2024!'
    'host': 'localhost'
    'port': 5432
}

class EHRQuery:
    def __init__(self, user_id, source_ip='127.0.0.1'):
        """Initialise EHR query interface with user context"""
        self.user_id = user_id
        self.source_ip = source_ip
        self.conn = None
        self.cursor = None

        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            print(f"Connected to EHR database")
            print(f" User: {user_id}")
            print(f" Source: {source_ip}\n") 
        except Exception as e:
            print(f"Database connection failed: {e}")
            sys.exit(1)

    def log_access(self, patient_id, access_type, action, success=True):
        """Log data access to audit table"""
        try:
            query = """
            INSERT INTO access_logs (user_id, patient_id, access_type, source_ip,
                                     action, success, access_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
            """
            self.cursor.execute(query, (
                self.user_id,
                patient_id,
                access_type,
                self.source_ip,
                action,
                success
                datetime.now()
            ))
            self.conn.commit()
        except Exception as e:
            print(f"Audit log failed: {e}")

    def search_patients(self, last_name=None, first_name=None, date_of_birth=None):
        """Search for patients by name or DOB"""
        print(f"--- Searching Patients ---")

        conditions = []
        params = []

        if last_name:
            conditions.append("last_name ILIKE %s")
            params.append(f"%{last_name}%")

        if first_name:
            conditions.append("first_name ILIKE %s")
            params.append(f"%{first_name}%")

        if date_of_birth:
            conditions.append("date_of_birth = %s")
            params.append(date_of_birth)

        if not conditions:
            print("No search criteria provided")
            return []

        where_clause = " AND ".join(condtions)

        query = f"""
        SELECT patient_id, first_name, last_name, date_of_birth, gender,
               city, state, phone

        FROM patients
        WHERE {where_clause}
        ORDER BY last_name, first_name
        LIMIT 20;
        """

        try:
            self.cursor.execute(query, params)
            results = self.cursor.fetchall()