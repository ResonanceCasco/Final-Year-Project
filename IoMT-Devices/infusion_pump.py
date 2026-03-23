#!/usr/bin/env python3
"""
Infusion Pump IoMT Device SImulator
Simulates medication infusion pump sending dosage data to EHR system
"""

import time
import random
import requests
import json
from datetime import datetime
import sys

# Device Configuration
DEVICE_ID = "PUMP-001"
DEVICE_NAME = "Infusion Pump - Room 301"
PATIENT_ID = "test-patient-001"

# EHR Server Configuration
EHR_API_URL = "https://192.168.40.20:5000/api/infusion" # DATA VLAN EHR server
TRANSMIT_INTERVAL = 30 # seconds between transmissions

# Medication Database (simulated)
MEDICATIONS = {
    "morphine": {
        "name": "Morphine Sulfate",
        "concentration": 1.0, # mg/mL
        "max_rate": 10.0, # mL/hr
        "safe_dose_range": (0.5,5.0) # mg/hr
    },
    "saline": {
        "name": "Normal Saline 0.9%",
        "concentration": 9.0, # mg/mL (sodium chloride)
        "max_rate": 1000.0, # mL/hr
        "safe_dose_range": (50,500) # mL/hr
    },
    "insulin": {
        "name": "Regular Insulin",
        "concentration": 1.0, # units/mL
        "max_rate": 10.0, # mL/hr
        "safe_dose_range": (0.5,10.0) # units/hr
    },
    "heparin": {
        "name": "Heparin Sodium",
        "concentration": 1000.0, # units/mL
        "max_rate": 25.0, # mL/hr
        "safe_dose_range": (1000, 2000) # units/hr
    }
}

class InfusionPump:
    def __init__(self, device_id, patient_id, medication="saline"):
        """Initialise infusion pump"""
        self.device_id = device_id
        self.patient_id = patient_id
        self.is_running = False
        self.is_infusing = False

        # Current medication
        if medication not in MEDICATIONS:
            print(f"Unknown medication '{medication}', defaulting to saline")
            medication = "saline"

        self.current_medication = medication
        self.medication_info = MEDICATIONS[medication]

        # Infusion parameters
        self.flow_rate = 0.0 # mL/hr
        self.volume_infused = 0.0 # mL total
        self.volume_remaining = 500.0 # mL in bag
        self.pressure = 0 # mmHg

        # Alarms
        self.alarms = []

        print(f"  Infusion Pump initialised")
        print(f"  Device ID: {self.device_id}")
        print(f"  Patient: {self.patient_id}")
        print(f"  Medication: {self.medication_info['name']}")
        print(f"  Transmit Interval: {TRANSMIT_INTERVAL}s")
        print()

    def start_infusion(self, flow_rate):
        """Start infusion at specified flow rate"""
        if flow_rate > self.medication_info['max_rate']:
            self.alarms.append(f"CRITICAL: Flow rate exceeds maximum ({self.medication_info['max_rate']} mL/hr)")
            return False

        if flow_rate <= 0:
            self.alarms.append("ERROR: Invalid flow rate")
            return False

        self.flow_rate = flow_rate
        self.is_infusing = True
        self.alarms.clear()

        print(f"Infusion started at {flow_rate} mL/hr")
        return True

    def stop_infusion(self):
        """Stop infusion"""
        self.is_infusing = False
        self.flow_rate = 0.0
        print(f"Infusion stopped")

    def update_infusion(self, elapsed_seconds):
        """Update infusion state based on time elapsed"""
        if not self.is_infusing:
            return

        # Calculate volume infused in this interval
        hours_elapsed = elapsed_seconds / 3600.0
        volume_delta = self.flow_rate * hours_elapsed

        # Update volumes 
        self.volume_infused += volume_delta
        self.volume_remaining -= volume_delta

        # Update pressure (simulate IV line pressure)
        self.pressure = random.randint(5,15) # Normal range 5-15 mmHg

        # Simulate occasional pressure spike (occlusion)
        if random.random() < 0.02: # 2% chance
            self.pressure = random .randint(20, 40)

        # Check for alarms
        self.check_alarms()

        # Auto-stop if bag empty
        if self.volume_remaining <= 0:
            self.volume_remaining = 0
            self.stop_infusion()
            self.alarms.append("INFO: Infusion complete - bag empty")

    def check_alarms(self):
        """Check for alarm conditions"""
        self.alarms.clear()

        # High pressure alarm (occlusion)
        if self.pressure > 20:
            self.alarms.append("WARNING: High pressure detected - check IV line")

        # Low volume alarm 
        if self.volume_remaining < 50:
            self.alarms.append("WARNING: Low volume - bag nearly empty")

        # Dose safety check
        # For saline, check flow_rate directly; for meds, check dose
        if self.current_medication == "saline":
            dose_rate = self.flow_rate
        else:
            dose_rate = self.flow_rate * self.medication_info['concentration']

        safe_min, safe_max = self.medication_info['safe_dose_range']

        if dose_rate < safe_min:
            self.alarms.append(f"CAUTION: Dose rate below reccomended range")
        elif dose_rate > safe_max:
            self.alarms.append(f"CRITICAL: Dose rate exceeds safe maximum")

    def collect_pump_data(self):
        """Collect current pump status and parameters"""
        if self.current_medication == "saline":
            dose_rate = self.flow_rate
            dose_unit = "mL/hr"
        else:
            dose_rate = self.flow_rate * self.medication_info['concentration']
            dose_unit = "mg/hr" if self.current_medication == "morphine" else "units/hr"

        data = {
            "device_id": self.device_id,
            "patient_id": self.patient_id,
            "timestamp": datetime.now().isoformat(),
            "pump_status": {
                "is_infusing": self.is_infusing,
                "medication": {
                    "name": self.medication_info['name'],
                    "concentration": self.medication_info['concentration']
                },
                "flow_rate": {
                    "value": round(self.flow_rate, 2),
                    "unit": "mL/hr"
                },
                "dose_rate": {
                    "value": round(dose_rate, 2),
                    "unit": dose_unit
                },
                "volume_infused": {
                    "value": round(self.volume_infused, 2),
                    "unit": "mL"
                },
                "volume_remaining": {
                    "value": round(self.volume_remaining, 2),
                    "unit": "mL"
                },
                "pressure": {
                    "value": self.pressure,
                    "unit": "mmHg",
                    "status": "high" if self.pressure > 20 else "normal"
                },
                "alarms": self.alarms
            }
        }

        return data

    def transmit_data(self, data):
        """Transmit pump data to EHR server"""
        try:
            # Simulate API call
            try:
                headers = {
                    "Content-Type": "application/json",
                    "X-Device-ID": self.device_id
                }

                response = requests.post(
                    EHR_API_URL,
                    json=data,
                    timeout=5,
                    headers=headers
                )

                if response.status_code == 200:
                    print(f"   Transmitted to EHR server")
                    return True
                else:
                    print(f"   Server error: {response.status_code}")

            except requests.exceptions.RequestException:
                # Server not available - save locally instead
                pass

            # Save to local file as fallback
            self._save_local(data)
            return True

        except Exception as e:
            print(f"   Transmission failed: {e}")
            return False

    def _save_local(self, data):
        """Save pump data to local file"""
        filename = f"infusion_log_{self.device_id}.json"

        try:
            # Load existing data
            try:
                with open(filename, 'r') as f:
                    log_data = json.load(f)
            except FileNotFoundError:
                log_data = []

            # Append new data 
            log_data.append(data)

            # Save back
            with open(filename, 'w') as f:
                json.dump(log_data, f, indent=2, default=str)

            print(f"   Saved locally to {filename}")

        except Exception as e:
            print(f"   Local save failed: {e}")

    def display_status(self, data):
        """Display pump status on console"""
        status = data['pump_status']

        print(f"\n{'='*60}")
        print(f"INFUSION PUMP STATUS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        print(f"Device: {self.device_id} | Patient: {self.patient_id}")
        print(f"{'-'*60}")

        # Infusion status
        infusing_icon = "running" if status['is_infusing'] else "stopped"
        print(f"{infusing_icon} Status: {'INFUSING' if status['is_infusing'] else 'STOPPED'}")
        print(f" Medication: {status['medication']['name']}")
        print(f" Concentration: {status['medication']['concentration']} mg/mL")
        print()

        # Flow parameters
        print(f" Flow Rate: {status['flow_rate']['value']} {status['flow_rate']['unit']}")
        print(f" Dose Rate: {status['dose_rate']['value']} {status['flow_rate']['unit']}")
        print()

        # Volumes
        print(f" Volume Infused: {status['volume_infused']['value']} {status['volume_infused']['unit']}")
        print(f" Volume Remaining: {status['volume_remaining']['value']} {status['volume_remaining']['unit']}")
        print()

        # Pressure
        pressure_icon = "CAUTION" if status ['pressure']['status'] == "high" else "Safe"
        print(f"{pressure_icon} Pressure: {status['pressure']['value']} {status['pressure']['unit']} [{status['pressure']['status']}]")

        # Alarms 
        if status['alarms']:
            print(f"\n ALARMS ({len(status['alarms'])}):")
            for alarm in status['alarms']:
                print(f"   {alarm}")

        print(f"{'='*60}\n")

    def run(self, duration=None):
        """
        Run continuous pump monitoring
        duration: Run for X seconds (None = run indefinitely)
        """
        self.is_running = True
        start_time = time.time()
        transmission_count = 0
        last_update = time.time()

        print(f"{'='*60}")
        print(f"Infusion Pump Started")
        print(f"{'='*60}")

        # Pormpt for flow rate
        while True:
            try:
                flow_rate = float(input(f"Enter flow rate (mL/hr, max {self.medication_info['max_rate']}): "))
                if self.start_infusion(flow_rate):
                    break
            except ValueError:
                print("Invalid input. Please enter a number.")

        print("\nPress Ctrl+C to stop\n")

        try:
            while self.is_running:
                current_time = time.time()
                elapsed = current_time - last_update

                # Update infusion state
                self.update_infusion(elapsed)
                last_update = current_time

                # Collect data
                data = self.collect_pump_data()

                # Display
                self.display_status(data)

                # Transmit 
                if self.transmit_data(data):
                    transmission_count += 1

                # Check duration
                if duration and (time.time() - start_time) >= duration:
                    break

                # Stop if infusion complete
                if not self.is_infusing and self.volume_remaining <= 0:
                    print("Infusion complete - stopping pump\n")
                    break

                # Wait before next update
                print(f"Next update in {TRANSMIT_INTERVAL} seconds...\n")
                time.sleep(TRANSMIT_INTERVAL)

        except KeyboardInterrupt:
            print("\n\nPump stopped by user")
            self.stop_infusion()

        finally:
            self.is_running = False
            elapsed = time.time() - start_time

            print(f"\n{'='*60}")
            print(f"Infusion Session Summary")
            print(f"{'='*60}")
            print(f"Total Runtime: {elapsed:.0f} seconds")
            print(f"Volume Infused: {self.volume_infused:.2f} mL")
            print(f"Transmissions: {transmission_count}")
            print(f"{'='*60}\n")

if __name__ == "__main__":
    print("="*60)
    print("IoMT Infusion Pump Simulator")
    print("="*60)
    print()

    # Check for command line arguments
    medication = "saline"
    duration = None

    if len(sys.argv) > 1:
        medication = sys.argv[1]
    if len(sys.argv) > 2:
        try:
            duration = int(sys.argv[2])
            print(f"Demo Mode: Running for {duration} seconds\n") 
        except ValueError:
            pass

    # Initialise and run pump 
    pump = InfusionPump(
        device_id=DEVICE_ID,
        patient_id=PATIENT_ID,
        medication=medication
    ) 

    pump.run(duration=duration)
            

