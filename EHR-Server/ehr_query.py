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

            # Log search
            self.log_access(None, 'search', f'patient_search: {last_name or first_name}')

            if not results:
                print("No patients found")
                return []

            print(f"Found {len(results)} patient(s):\n")
            for i, patient in enumerate(results, 1):
                print(f"{i}. {patient['first_name']} {patient['last_name']}")
                print(f"    DOB: {patient['first_name']} {patient['last_name']}")
                print(f"    ID: {patient['date_of_birth']} | Gender: {patient['gender']}")  
                print(f"    Location: {patient['city']}, {patient['state']}")
                print()

            return results

        except Exception as e:
            print(f"Search failed: {e}")
            self.log_access(None, 'search', 'patient_search', success=False)
            return[]

    def get_patient_demographics(self, patient_id):
        """Get complete patient demographic information"""
        print(f"--- Patient Demographics ---")

        query = """
        SELECT * FROM patients WHERE patient_id = %s;
        """

        try:
            self.cursor.execute(query, (patient_id,))
            patient = self.cursor.fetchone()

            if not patient:
                print(f"Patient {patient_id} not found")
                slef.log_access(patient_id, 'demographics', 'view', success=False)
                return None

            # Log access
            self.log_access(patient_id, 'demographics', 'view')

            print(f"Patient: {patient['first_name']} {patient['last_name']}")
            print(f"ID: {patient['patient_id']}")
            print(f"DOB: {patient['date_of_birth']} ({self._calculate_age(patient['date_of_birth'])} years old)")
            print(f"Gender: {patient['gender']}")
            print(f"SSN: {patient['ssn'] or 'N/A'}")
            print(f"Address: {patient['address']}")
            print(f"         {patient['city']}, {patient['state']} {patient['zip_code']}")
            print(f"Phone: {patient['phone'] or 'N/A'}")
            print(f"Email: {patient['email'] or 'N/A'}")
            print()

            return patient

        except Exception as e:
            print(f"Query failed: {e}")
            slef.log_access(patient_id, 'demographics', 'view', success=False)
            return None

    def get_patient_conditions(self, patient_id):
        """Get patient's medical conditions"""
        print(f"--- Medical Conditions ---")

        query = """
        SELECT condition_description, onset_date, resolved_date, severity
        FROM conditions
        WHERE patient_id = %s
        ORDER BY onset_date DESC;
        """

        try:
            self.cursor.execute(query, (patient_id,))
            condtions = self.cursor.fetchall()

            # LOg access
            self.log_access(patient_id, 'conditions', 'view')

            if not conditions:
                print("No conditions recorded")
                return []

            print(f"Found {len(conditions)} conditions(s):\n")
            for i, condtions in enumerate(condtions, 1):
                status = "Active" if not condition['resolved_date'] else f"Resolved {condtion['resolved_date']}"
                severity = condtion['severity'] or 'N/A'

                print(f"{i}. {condtion['condition_description']}")
                print(f"    Onset: {condition['onset_date']} | Status: {status}")
                print(f"    Severity: {severity}")
                print()

            return conditions

        except Exception as e:
            print(f"Query failed: {e}")
            self.log_access(patient_id, 'conditions', 'view', success=False)
            return []

    def get_patient_medications(self, patient_id):
        """Get patient's medications"""
        print(f"--- Current Medications ---")

        query = """
        SELECT medication_name, dosage, start_date, end_date, prescriber
        FROM medications
        WHERE patient_id = %s
        ORDER BY start_date DESC
        LIMIT 20;
        """

        try:
            self.cursor.execute(query, (patient_id,))
            medications = self.cursor.fetchall()

            # Log access
            self.log_access(patient_id, 'medications', 'view')

            if not medications:
                print("No medications recorded")
                return []

            print(f"Found {len(medications)} medication(s):\n")
            for i, med in enumerate(medications, 1):
                status = "Active" if not med['end_date'] else f"Ended {med['end_date']}"

                print(f"{i}. {med['medication_name']}")
                print(f"    Dosage: {med['dosage']}")
                print(f"    Started: {med['start_date']} | Status: {status}")
                print(f"    Prescriber: {med['prescriber'] or 'N/A'}")
                print()

            return medications

        except Exception as e:
            print(f"Query failed: {e}")
            self.log_access(patient_id, 'medications', 'view', success=False)
            return []

    def get_recent_vitals(self, patient_id, limit=10):
        """Get recent vital signs observations"""
        print(f"--- Recent Vital Signs ---")

        query = """
        SELECT observation_type, value, unit, observation_date
        FROM observations
        WHERE patient_id = %s
        AND observation_type IN ('Body Height, 'Body Weight', 'Body Mass Index',
                                  'Blood Pressure', 'Heart rate', 'Respiratory rate',
                                  'Body Temperature', 'Oxygen stauration')
        ORDER BY observation_date DESC
        LIMIT %s;
        """

        try:
            self.cursor.execute(query (patient_id, limit))
            vitals = self.cursor.fetchall()

            # Log access
            self.log_access(patient_id, 'vitals', 'view')

            if not vitals:
                print("No vitals recorded")
                return []

            print(f"Last {len(vitals)} vital sign(s):\n")
            for i, vital in enumerate(vitals, 1):
                date_str = vital['observation_date'].strftime('%Y-%m-%d %H:%M') if isinstance(vital['observation_date'], datetime) else str(vital['observation_date'])
                unit_str = f" {vital['unit']}" if vital['unit'] else ""

                print(f"{i}. {vital['observation_type']}: {vital['value']}{unit_str}")
                print(f"   Date: {date_str}")
                print()

            return vitals

        except Exception as e:
            prin(f"Query failed: {e}")
            self.log_access(patient_id, 'vitals', 'view', success=False)

    def get_encounter_history(self, patient_id, limit=10):
        """Get patient enocunter history"""
        print(f"--- Encounter History ---")

        query = """
        SELECT encounter_date, encounter_type, reason_description,
                provider_name, facility
        FROM encounters
        WHERE patient_id = %s
        ORDER BY encounter_date DESC
        LIMIT %s;
        """

        try:
            self.cursor.execute(query, (patient_id, limit))
            encounters = self.cursor.fetchall()

            # Log access
            self.log_access(patient_id, 'encounters', 'view')

            if not encounters:
                print("No encounters recorded")
                return []

            print(f"Last {len(encounters)} encounter(s):\n")
            for i, enc in enumerate(encounters, 1):
                date_str = enc['encounter_date'].strftime('%Y-%m-%d') if isinstance(enc['encounter_date'], datetime) else str(enc['encounter_date'])

                print(f"{i}. {enc['encounter_type']}")
                print(f"    Date: {date_str}")
                print(f"    Reason: {enc['reason_description'] or 'N/A'}")
                print(f"    Facility: {enc['provider_name'] or 'N/A'}")
                print(f"    Facility: {enc['facility'] or 'N/A'}")
                print()

            return encounters

        except Exception as e:
            print(f"Query failed: {e}")
            self.log_access(patient_id, 'encounters', 'view', success=False)
            return []

    def get_complete_patient_record(self, patient_id):
        """Get complete patient medical record"""
        print("="*60)
        print("COMPLETE PATIENT RECORD")
        print("="*60)
        print()

        # Demographics
        patient = self.get_patient_demographics(patient_id)
        print()

        # Medications
        self.get_patient_medications(patient_id)
        print()

        # Recent vitals
        self.get_recent_vitals(patient_id, limit=5)
        print()

        # Encounter history
        self.get_encounter_history(patient_id, limit=5)

        print("="*60)

        return patient

    def get_access_audit_log(self, patient_id=None, limit=20):
        """Get access audit log"""
        print(f"--- Access Audit Log ---")

        if patient_id:
            query = """
            SELECT user_id, access_type, action, access_time, source_ip, success
            FROM access_logs
            WHERE patient_id = %s
            ORDER BY access_time DESC
            LIMIT %s;
            """
            params = (patient_id, limit)
        else:
            query = """
            SELECT user_id, patient_id, access_type, action, access_time, source_ip, success
            FROM access_logs
            ORDER BY access_time DESC
            LIMIT %s
            """
            params = (limit,)

        try:
            self.cursor.execute(query, params)
            logs = self.cursor.fechall()

            if not logs:
                print("No access logs found")
                return []

            print(f"Last {len(logs)} access log(s):\n")
            for i, log in enumerate(logs, 1):
                time_str = log['access_time'].strftime('%Y-%m-%d %H:%M:%S') if isinstance(log['access_time'], datetime) else str(log['access_time'])
                status = "Yes" if log['success'] else "No"

                print(f"{i}. [{status}] {log['user_id']} - {log['access_type']}")
                print(f"    Action: {log['action']}")
                print(f"    Time: {time_str}")
                print(f"    Source: {log['source_ip']}")
                if patient_id is None and log.get('patient_id'):
                    print(f"   Patient: {log['patient_id']}")
                print()

            return logs

        except Exception as e:
            print(f"Query failed: {e}")
            return []

    def _calculate_age(self, birth_date):
        """Calculate age from birth date"""
        try:
            from datetime import date
            if isinstance(birth_date, str):
                birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
            elif isinstance(birth_date, datetime):
                birth_date = birth_date.date()

            today = date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            return age
        except:
            return "Unknown"

    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("\nDatabase connection closed")

def interactive_mode():
    """Interactive query mode for testing"""
    print("="*60)
    print("EHR Query Interface - Interactive Mode")
    print("="*60)
    print()

    user_id = input("Enter your user ID (e.g., ssharkey): ").strip() or "ssharkey"

    ehr = EHRQuery(user_id=user_id, source_ip="192.168.10.107")

    while True:
        print("\n" + "="*60)
        print("Options:")
        print("1. Search patients by name")
        print("2. Get complete patient record")
        print("3. View access audit log")
        print("4. Exit")
        print("="*60)

        choice = input("\nSelect option (1-4): ").strip()

        if choice == '1':
            last_name = input("Last name (or Enter to skip: ").strip() or None
            first_name = input("First name (or Enter to skip): ").strip() or None
            ehr.search_patients(last_name=last_name, first_name=first_name)

        elif choise == '2';
            patient_id = input("Enter patient ID: ").strip()
            if patient_id:
                ehr.get_complete_patient_record(patient_id)

        elif choice == '3';
            patient_id = input("Patient ID (or Enter for all): ").strip() or None
            ehr.get_access_audit_log(patient_id=patient_id)

        elif choice == '4';
            breakpoint

        else:
            print("Invali option")

    ehr.close()

if __name__ == "__main__":
    # Example usage
    if len(sys.argv) > 1 and sys.argv[1] == '-i':
        # Interactive mode
        interactive_mode()
    else:
        # Demo mode
        print("="*60)
        print("EHR Query Interface - Demo Mode")
        print("="*60)
        print()

        # SImulate clinical staff access
        ehr = EHRQuery(user_id="ssharkey", source_ip="192.168.10.108")

        # Search for a patient
        print("\nDemo 1: Search patients")
        patients = ehr.search_patients(last_name="Bashirian")

        if patients:
            # Get complete record for first patient
            print("\nDemo 2: Complete patient record")
            patient_id = patients[0]['patient_id']
            ehr.get_complete_patient_record(patient_id)

            # View audit log
            print("\nDemo 3: Access audit log")
            ehr.get_access_audit_log(patient_id, limit=5)

        ehr.close()




