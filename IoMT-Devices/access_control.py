#!/usr/bin/env python3
"""
Access Control IoMT Device Simulator
Simulates RFID badge reader for physical security integration
"""

import time
import random
import requests
import json
from datetime import datetime
import sys

# Device Configuration
DEVICE_ID = "RFID-READER-001"
DEVICE_NAME = "RFID Badge Reader - ICU Entrance"
LOCATION = "Intensive Care Unit - Main Door"

# EHR Server Configuration
EHR_API_URL = "http://192.168.40.20:5000/api/access" # DATA VLAN EHR server
BLOCKCHAIN_LOG_URL = "http://192.168.40.20:5000/api/blockchain/log"

# Authorised personnel database (simulated)
AUTHORISED_BADGES = {
    "BADGE-001": {
        "name": "Dr. Gregory House",
        "employee_id": "ghouse",
        "role": "Doctor",
        "department": "ICU",
        "clearance_level": 3
    },
    "BADGE-002": {
        "name": "Shaun Sharkey",
        "employee_id": "ssharkey",
        "role": "Nurse",
        "department": "ICU",
        "clearance_level": 2
    },
    "BADGE-003": {
        "name": "Mildred Ratched",
        "employee_id": "mratched",
        "role": "Nurse",
        "department": "Emergency",
        "clearance_level": 2
    },
    "BADGE-004": {
        "name": "Wallace Breen",
        "employee_id": "wbreen",
        "role": "IT Admin",
        "department": "IT",
        "clearance_level": 4
    },
    "BADGE-005": {
        "name": "Barney Calhoun",
        "employee_id": "bcalhoun",
        "role": "Janitor",
        "department": "Facillities",
        "clearance_level": 1
    }
}

# Required clearance level for this location
REQUIRED_CLEARANCE = 2 # ICU requires level 2+

class AccessControl:
    def __init__(self, device_id, location):
        """Initialise access control reader"""
        self.device_id = device_id
        self.location = location
        self.is_running = False

        # Access log
        self.access_attempts = []
        self.total_granted = 0
        self.total_denied = 0

        print(f"  Access Control Reader initialised")
        print(f"  Device ID: {self.device_id}")
        print(f"  Location: {self.location}")
        print(f"  Required Clearance: Level {REQUIRED_CLEARANCE}")
        print()

    def simulate_badge_scan(self):
        """Simulate a random badge scan"""
        # 80% chance authorised badge, 20% chance unknown badge
        if random.random() < 0.8:
            badge_id = random.choice(list(AUTHORISED_BADGES.keys()))
        else:
            badge_id = f"UNKNOWN-{random.randint(100, 999)}"

        return badge_id

    def verify_access(self, badge_id):
        """Verify if badge has access to this location"""
        timestamp = datetime.now()

        # Check if badge is authorised
        if badge_id not in AUTHORISED_BADGES:
            result = {
                "badge_id": badge_id,
                "authorised": False,
                "reason": "Unknown badge",
                "timestamp": timestamp.isoformat(),
                "action": "DENY"
            }
            self.total_denied += 1
            return result

        # Get badge info
        badge_info = AUTHORISED_BADGES[badge_id]

        # Check clearance level
        if badge_info["clearance_level"] < REQUIRED_CLEARANCE:
            result = {
                "badge_id": badge_id,
                "employee_id": badge_info["employee_id"],
                "name": badge_info["name"],
                "role": badge_info["role"],
                "clearance_level": badge_info["clearance_level"],
                "authorised": False,
                "reason": f"Insufficient clearance (has {badge_info['clearance_level']}, needs {REQUIRED_CLEARANCE})",
                "timestamp": timestamp.isoformat(),
                "action": "DENY"
            }
            self.total_denied += 1
            return result

        # Access granted
        result = {
            "badge_id": badge_id,
            "employee_id": badge_info["employee_id"],
            "name": badge_info["name"],
            "role": badge_info["role"],
            "clearance_level": badge_info["clearance_level"],
            "authorised": True,
            "reason": "Access granted",
            "timestamp": timestamp.isoformat(),
            "action": "GRANT"
        }
        self.total_granted += 1
        return result

    def log_access_event(self, access_result):
        """Create access event for logging"""
        event = {
            "device_id": self.device_id,
            "location": self.location,
            "timetsamp": access_result["timestamp"],
            "badge_id": access_result["badge_id"],
            "name": access_result.get("name"),
            "role": access_result.get("role"),
            "clearance_level": access_result.get("clearance_level"),
            "authorised": access_result["authorised"],
            "action": access_result["action"],
            "reason": access_result["reason"]
        }

        self.access_attempts.append(event)
        return event

    def transmit_event(self, event):
        """Transmit access event to EHR/blockchain"""
        try:
            # Simulate API call
            try:
                headers = {
                   "Content-Type": "application/json",
                   "X-Device-ID": self.device_id
                }

                response = requests.post(
                    EHR_API_URL,
                    json=event,
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
            self._save_local(event)
            return True

        except Exception as e:
            print(f"   Transmission failed: {e}")
            return False

    def _save_local(self, event):
        """Save access event event to local file"""
        filename = f"access_log_{self.device_id}.json"

        try:
            # Load existing data
            try:
                with open(filename, 'r') as f:
                    log_data = json.load(f)
            except FileNotFoundError:
                log_data = []

            # Append new event
            log_data.append(event)

            # Save back
            with open(filename, 'w') as f:
                json.dump(log_data, f, indent=2, default=str)

            print(f"   Saved locally to {filename}")

        except Exception as e:
            print(f"   Local save failed: {e}")

    def display_access_event(self, event):
        """Display access event on console"""
        print(f"\n{'='*60}")
        print(f"ACCESS EVENT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        print(f"Location: {self.location}")
        print(f"{'-'*60}")

        # Badge info
        print(f"Badge ID: {event['badge_id']}")

        if event.get('name'):
            print(f"Name: {event['name']}")
            print(f"Employee ID: {event['name']}")
            print(f"Role: {event['role']}")
            print(f"Clearance Level: {event['clearance_level']}")

        # Access decision
        if event['authorised']:
            print(f"\n  ACCESS GRANTED")
            print(f"  Door unlocked")
        else:
            print(f"\n  ACCESS DENIED")
            print(f"  Reason: {event['reason']}")
            print(f"  Door remains locked")

        print(f"{'='*60}\n")

    def display_summary(self):
        """Display access statistics"""
        total = self.total_granted + self.total_denied
        grant_pct = (self.total_granted / total * 100) if total > 0 else 0

        print(f"\n{'='*60}")
        print(f"ACCESS CONTROL STATISTICS")
        print(f"{'='*60}")
        print(f"Total Attempts: {total}")
        print(f"Granted: {self.total_granted} ({grant_pct:.1f}%)")
        print(f"Denied: {self.total_denied} ({100-grant_pct:.1f}%)")
        print(f"{'='*60}\n")

    def run_simulation(self, num_scans=10, interval=5):
        """
        Run automatic simulations 
        num_scans: Number of badge scans to simulate
        interval: Seconds between scans
        """
        self.is_running = True

        print(f"{'='*60}")
        print(f"Access Control Simulation Started")
        print(f"{'='*60}")
        print(f"Simulating {num_scans} badge scans")
        print(f"Interval: {interval} seconds")
        print(f"\nPress Ctrl+C to stop early\n")

        try:
            for i in range(num_scans):
                print(f"Scan {i+1}/{num_scans}:")

                # Simulate badge scan
                badge_id = self.simulate_badge_scan()
                print(f"  Badge scanned: {badge_id}")

                # Verify access
                access_result = self.verify_access(badge_id)

                # Log event 
                event = self.log_access_event(access_result)

                # Display
                self.display_access_event(event)

                # Transmit
                self.transmit_event(event)

                # Wait before next scan (unless last one)
                if i < num_scans - 1:
                    print(f"Next scan in {interval} seconds...\n")
                    time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\nSimulation stopped by user")

        finally:
            self.is_running = False
            self.display_summary()

    def run_interactive(self):
        """Run in interactive mode"""
        self.is_running = True

        print(f"{'=*60'}")
        print(f"Access Control - Interactive Mode")
        print(f"{'='*60}")
        print(f"Enter badge IDs to simulate scans")
        print(f"Type 'random' for random badge")
        print(f"Type 'list' to see authorised badges")
        print(f"Type 'stats' to see statistics")
        print(f"Type 'quit' to exit\n")

        while self.is_running:
            try:
                user_input = input("Badge ID: ").strip()

                if user_input.lower() == 'quit':
                    break

                elif user_input.lower() == 'random':
                    badge_id = self.simulate_badge_scan()
                    print(f"  Simulated badge: {badge_id}")

                elif user_input.lower() == 'list':
                    print("\nAuthorised Badges:")
                    for badge_id, info in AUTHORISED_BADGES.items():
                        print(f"  {badge_id}: {info['name']} ({info['role']}, Level {info['clearance_level']})")
                    print()
                    continue

                elif user_input.lower() == 'stats':
                    self.display_summary()
                    continue

                else:
                    badge_id = user_input

                # Verify access
                access_result = self.verify_access(badge_id)

                # Log event 
                event = self.log_access_event(access_result)

                # Display
                self.display_access_event(event)

                # Transmit
                self.transmit_event(event)

            except KeyboardInterrupt:
                print("\n\nExiting...")
                break

        self.is_running = False
        self.display_summary()

if __name__ == "__main__":
    print("="*60)
    print("IoMT Access Control Simulator")
    print("="*60)
    print()

    # Initialise reader
    reader = AccessControl(
        device_id=DEVICE_ID,
        location=LOCATION
    )

    # Check for mode
    if len(sys.argv) > 1:
        if sys.argv[1] == '-i':
            # Interactive mode
            reader.run_interactive()
        elif sys.argv[1] == '-s':
            # Simulation mode
            num_scans = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            interval = int (sys.argv[3]) if len(sys.argv) > 3 else 5
            reader.run_simulation(num_scans=num_scans, interval=interval)
    else:
        # Default: simulation with 5 scans
        reader.run_simulation(num_scans=5, interval=3)
            









                
                


