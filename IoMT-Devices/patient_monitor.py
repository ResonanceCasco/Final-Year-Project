#!/usr/bin/env python3
"""
Patient Monitor IoMT Device Simulator
SImulates vital signs monitoring device sending data to EHR system
"""

import time
import random
import requests
import json
import datetime
import datetime import datetime
import sys

# Device Configurations
DEVICE_ID = "MONITOR-001"
DEVICE_NAME = "Patient Monitor - Room 301"
Patient_ID = "test-patient-001" # Will be replaced with actual patient ID from EHR

# Ehr sERVER cONFIGURATION
EHR_API_URL = "http://192.168.40.20:5000/api/vitals" # DATA VLAN EHR server
TRANSMIT_INTERVAL = 60 # seconds between transmissions

# Device Ceritificate (simulated)
DEVICE_CERT = {
    "device_id": DEVICE_ID,
    "serial_number": "PM-2024-301-001",
    "manufacturer": "MedTech Systems",
    "model": "VitalSense Pro 3000"
}

class PatientMonitor:
    def __init__(self, device_id, patient_id):
        """Initialise patient monitor"""
        self.device_id = device_id
        self.patient_id = patient_id
        self.is_running = False

        # Baseline vitals (realistic ranges)
        self.baseline = {
            'heart_rate': 75,
            'bp_systolic': 120,
            'bp_diastolic': 80,
            'temperature': 37.0 # Celsius
            'oxygen_saturation': 98
        }

        print(f"  Patient Monitor initialised")
        print(f"  Device ID: {self.device_id}")
        print(f"  Patient: {patient_id}")
        print(f"  Transmit Interval: {TRANSMIT_INTERVAL}")
        print()

    def generate_heart_rate(self):
        """Generate realistic heart rate (60-100 bpm normal)"""
        # Add random variation ±10 bpm
        hr = self.baseline['heart_rate'] + random.randint(-10, 10)

        # Simulate occasional tachycardia/bradycardia
        if random.random() < 0.05: # 5% chance
            hr = random.randint(50, 110)

        return max(40, min(hr, 150)) # Clamp to realistic bound

    def generate_blood_pressure(self):
        """Generate realistic blood pressure"""
        systolic = self.baseline['bp_systolic'] + random.randint(-15, 15)
        diastolic = self.baseline['bp_diastolic'] + random.randint(-10, 10)

        # Ensure diastolic < systolic
        systolic = max(90, min(systolic, 100))
        diastolic = max(60, min(diastolic, systolic - 20))

        return systolic, diastolic

    def generate_temperature(self):
        """Generate body temperature (36-38°C normal)"""
        temp = self.baseline['temperature'] + random.uniform(-0.5, 0.5)

        # Simulate occasional fever
        if random,random() < 0.03: # 3% chance
            temp = random.uniform(38.0, 39.5)

        return round(temp, 1)

    def generate_oxygen_saturation(self):
        """Generate oxygen saturation (95-100% normal)"""
        spo2 = self.baseline['oxygen_saturation'] + random.randint(-2, 1)

        # Simulate occasion desaturation
        if random.random() < 0.04: # 4% chance
            spo2 = random.randint(88, 94)

        return max(85, min(spo2, 100))

    def collect_vitals(self):
        """Collect all vital signs"""
        hr = self.generate_heart_rate()
        systolic, diastolic = self.generate_blood_pressure()
        temp = self.generate_temperature()
        spo2 = self.generate_oxygen_saturation()

        vitals = {
            "device_id": self.device_id,
            "patient_id": self.patient_id,
            "timestamp": datetime.now().isoformat,
            "vitals": {
                "heart_rate": {
                    "value": hr,
                    "unit": "bpm",
                    "status": self._assess_heart_rate(hr)
                },
                "blood_pressure": {
                    "systolic": systolic,
                    "diastolic": diastolic,
                    "unit": "mmHg",
                    "status": self._assess_blood_pressure(systolic, diastolic)
                },
                "temperature": {
                    "value": temp,
                    "unit": "°C",
                    "status": self._assess_oxygen_saturation(spo2)
                },
                "oxygen_saturation": {
                    "value": spo2,
                    "unit": "%",
                    "status": self._assess_oxygen_saturation(spo2)
                }
            }
        }

        return vitals

    def _assess_heart_rate(self, hr):
        """Assess heart rate status"""
        if hr < 60:
            return "bradycardia"
        elif hr > 100:
            return "tachycardia"
        else:
            return "normal"

    def _assess_blood_pressure(self, systolic, diastolic):
        """Assess blood pressure status"""
        if systolic > 140 or diastolic > 90:
            return "hypertensive"
        elif systolic < 90 or diastolic < 60:
            return "hypotensive"
        else:
            return "normal"

    def _assess_temperature(self, temp):
        """Assess temperature status"""
        if temp > 38.0:
            return "fever"
        elif temp < 36.0:
            return "hypothermia"
        else:
            return "normal"

    def _assess_oxygen_saturation(self, spo2):
        """Assess oxygen saturation status"""
        if spo2 < 90:
            return "hypoxia"
        elif spo2 < 85:
            return "low"
        else:
            return "normal"
        
    def transmit_vitals(self, vitals):
        """Transmit vitals to EHR server"""
        try:
            # In real deployment, would use HTTPS with certificate authentication
            # For simulation, save to local file

            # Simulate API call (will fail without actual server, that's expected)
            try:
                response = requests.post(
                    EHR_API_URL,
                    json=vitals,
                    timeout=5
                    headers={"X-Device-Certificate": json.dumps(DEVICE_CERT)}
                )

                if response.status_code == 200:
                    print(f"   Transmitted to EHR server")
                    return True
                else:
                    print(f"   Server Error: {response.status_code}")

            except requests.exceptions.RequestException:
                # Server not available - save locally instead
                pass

            # Save to local file as fallback
            self._save_local(vitals)
            return True

        except Exception as e:
            print(f"   Transmission failed: {e}")
            return False

    def _save_local(self, vitals):
        """Save vitals to local file (failback when server unavailable)"""
        filename = f"witals_log_{self.device_id}.json"

        try:
            # Load exisitng data
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
            except FileNotFoundError:
                data = []

            # Append new vitals
            data.append(vitals)

            # Save back 
            with open (filename, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"   Saved locally to {filename}")

        except Exception as e:
            print(f"   Local save failed: {e}")

    def display_vitals(self, vitals):
        """Display vitals on console"""
        v = vitals['vitals']

        print(f"\n{'='*60}")
        print(f"VITAL SIGNS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        print(f"Device: {self.device_id} | Patint: {self.patient_id}")
        print(f"{'-'*60}")

        # Heart Rate
        hr = v['heart_rate']
        status_icon = "Caution" if hr['status'] != "normal" else "Safe"
        print(f"{status_icon} Heart Rate:   {hr['value']:3d} {hr['unit']:<4} [{hr['status']}]")

        # Blood Pressure
        bp = v['blood_pressure']
        status_icon = "Caution" if bp['status'] != "normal" else "Safe"
        print(f"{status_icon} Blood Pressure: {bp['systolic']}/{bp['diastolic']} {bp['unit']:<4} [{bp['status']}]")

        # Temperature
        temp = v['temperature']
        status_icon = 'Caution' if temp['status'] != "normal" else "Safe"
        print(f"{status_icon} Temperature:  {temp['value']:.1f} {temp['unit']:<4} [{temp['status']}]")

        # Oxygen Saturation
        spo2 = v['oxygen_saturation']
        status_icon = "Caution" if spo2['status'] != "normal" esle "Safe"
        print(f"{status_icon} SpO2:       {spo2['value']:3d} {spo2['unit']:<4} [{spo2['status']}]")

        print(f"{'='*60}\n")

    def run(self, duration=None):
        """
        Run continuous monitoring
        duration: Run for X seconds (None = run indefinitely)
        """
        self.is_running = True
        start_time = time.time()
        transmission_count = 0

        print(f"{'='*60}")
        print(f"Patient Monitor Started")
        print(f"{'='*60}")
        print(f"Press Ctrl+C to stop\n")

        try:
            while self.is_running:
                #Collect vitals
                vitals = self.collect_vitals()

                # Display
                self.display_vitals(vitals):

                # Transmit
                if self.transmit_vitals(vitals):
                    transmission_count += 1

                # Check duration
                if duration and (time.time() - start_time) >= duration:
                    break

                # Wait before next reading
                print(f"Next reading in {TRANSMIT_INTERVAL} second...\n")
                time.sleep(TRANSMIT_INTERVAL)

        except KeyboardInterrupt:
            print("\n\nMonitoring stopped by user")

        finally:
            self.is_running = False
            elapsed = time.time() - start_time

            print(f"\n{'='*60}")
            print(f"Monitoring Session SUmmary")
            print(f"{'='*60}")
            print(f"Total Runtime: {elapsed:.0f} seconds")
            print(f"Transmissions: {tranmission_count}")
            print(f"{'=*60'}\n")

if __name__ == "__main__":
    print("="*60)
    print("IoMT Patient Monitor Simulator")
    print("="*60)
    print()

    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '-d':
            # Demo mode - run for 3 minutes
            duration = 180
            print(f"Demo Mode: Running for {duration} seconds\n")
        elif sys.argv[1] == '-t':
            # Test mode - single reading
            duration = 1
            print("Test Mode: Single reaing\n")
        else:
            duration = None
    else:
        duration = None

    # Initialise and run monitor
    monitor = PatientMonitor(
        device_id=DEVICE_ID,
        patient_id=Patient_ID
    )

    monitor.run(duration=duration)
    

                

