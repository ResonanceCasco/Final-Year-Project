#!/usr/bin/env python3
"""
Audit Trail Query Tool
Query and analyze authentication events from blockchain
"""

from solana.rpc.api import Client
from solders.keypair import Keypair
import json 
from datetime import datetime, timedelta
import os

# Configuration 
SOLANA_DEVNET_URL = "http://localhost:8899"
WALLET_PATH = "/home/jaboris/Documents/GitHub/Final-Year-Project/zero-trust-healthcare/blockchain-scripts/keys/audit-wallet.json"
LOG_DIR = "/home/jaboris/Documents/GitHub/Final-Year-Project/zero-trust-healthcare/blockchain-scripts/logs/"

class AuditQuery:
    def __init__(self):
        """Initialise audit query tool"""
        from solana.rpc.api import Client
        from solders.keypair import Keypair

        # Connect to local validator
        self.client = Client(SOLANA_DEVNET_URL)

        # Load keypair using the absolute path defined at top
        with open(WALLET_PATH, 'r') as f:
            keypair_data = json.load(f)
        self.keypair = Keypair.from_bytes(bytes(keypair_data))

        self.local_log_file = os.path.join(LOG_DIR, "audit_events.json")

        print(f"Audit Query Tool inistialised")
        print(f"Wallet: {self.keypair.pubkey()}\n")

        # For testing, use local log file
        self.local_log_file = os.path.join(LOG_DIR, "audit_events.json")

    def query_by_user(self, username):
        """Query all events for a specific user"""
        print(f"--- Query: Events for user '{username}' ---\n")

        events = self._load_local_events()
        user_events = [e for e in events if e.get('user') == username]

        if not user_events:
            print(f"No events found for user: {username}")
            return []

        print(f"Found {len(user_events)} event(s):\n")
        for i, event in enumerate(user_events, 1):
            self._display_event(i, event)

        return user_events

    def query_by_timerange(self, start_time, end_time=None):
        """Query events within a time range"""
        if end_time is None:
            end_time = datetime.now()

        print(f"--- Query: Events from {start_time} to {end_time} ---\n")

        events = self._load_local_events()

        # Filter by time
        filtered = []
        for event in events:
            event_time = datetime.fromisoformat(event.get('timestamp', ''))
            if start_time <= event_time <= end_time:
                filtered.append(event)

        print(f"Found {len(filtered)} event(s):\n")
        for i, event in enumerate(filtered, 1):
            self._display_event(i, event)

        return filtered

    def query_failed_logins(self, threshold=3):
        """Find users with multiple failed login attempts"""
        print(f"--- Query: Failed logins (threshold: {threshold}) --\n")

        events = self._load_local_events()

        # Count failed logins per user
        failed_counts = {}
        for event in events:
            if event.get('result') == 'failed' and event.get('action') == 'login':
                user = event.get('user')
                failed_counts[user] = failed_counts.get(user, 0) + 1

        # Filter by threshold
        suspicious = {user: count for user, count in failed_counts.items() if count >= threshold}

        if not suspicious:
            print(f"No users with {threshold}+ failed logins:")
            return[]

        print(f"Users with {threshold}+ failed logins:")
        for user, count in suspicious.items():
            print(f" - {user}: {count} failed attempts")

        return suspicious

    def query_high_risk_events(self, risk_threshold=50):
        """Find high-risk security events"""
        print(f"--- Query: High-risk events (score >= {risk_threshold}) ---\n")

        events = self._load_local_events()

        high_risk = [e for e in events if e.get('risk_score', 0) >= risk_threshold]

        if not high_risk:
            print(f"No high-risk events found")
            return []

        print(f"Found {len(high_risk)} high-risk event(s):\n")
        for i, event in enumerate(high_risk, 1):
            self._display_event(i, event)

        return high_risk

    def generate_timeline(self, username=None):
        """Generate chronological timeline of events"""
        print(f"--- Timeline: {'All events' if not username else f'Events for {username}'} ---\n")

        events = self._load_local_events()

        if username:
            events = [e for e in events if e.get('user') == username]

        # Sort by timestamp
        events.sort(key=lambda x: x.get('timestamp', ''))

        print(f"{'Time':<20} {'User':<15} {'Action':<10} {'Result':<10} {'Risk':<5}")
        print("-" * 70)

        for event in events:
            timestamp = event.get('timestamp', 'N/A')[:19] # Trim to datetime
            user = event.get('user', 'N/A')
            action = event.get('action', 'N/A')
            result = event.get('result', 'N/A')
            risk = event.get('risk_score', 0)

            print(f"{timestamp:<20} {user:<15} {action:<10} {result:<10} {risk:<5}")

        return events

    def _display_event(self, index, event):
        """Pretty print an event"""
        print(f"Event #{index}:")
        print(f"  User: {event.get('user')}")
        print(f"  Action: {event.get('action')}")
        print(f"  Result: {event.get('result')}")
        print(f"  Time: {event.get('timestamp')}")
        print(f"  Source IP: {event.get('source_ip')}")
        print(f"  Risk Score: {event.get('risk_score')}")
        print()

    def _load_local_events(self):
        """Load events from blockchain transactions"""
        print(" Querying blockchain for audit events...")

        try:
            from solders.signature import Signature

            # Get recent transaction signatures for our wallet
            # This fetches the last 1000 transactions
            signatures = self.client.get_signatures_for_address(
                self.keypair.pubkey(),
                limit=1000
            )

            if not signatures.value:
                print("  No transactions found on blockchain")
                return []

            events = []
            print(f" Found {len(signatures.value)} blockchain transactions")
            print(f" Parsing audit events...")

            # Fetch and parse each transaction
            for idx, sig_info in enumerate(signatures.value):
                try:
                    # The memo field always contains our JSON data!
                    if sig_info.memo:
                        # Format: "[length] {json_data}"
                        # Extract just the JSON part (after the length prefix)
                        memo_text = sig_info.memo

                        # Find the first { and extract from there
                        json_start = memo_text.find('{')
                        if json_start != -1:
                            json_str = memo_text[json_start:]

                            try:
                                event = json.loads(json_str)

                                # Add blockchain metadata
                                event['blockchain_signature'] = str(sig_info.signature)
                                event['block_time'] = sig_info.block_time

                                events.append(event)
                                print(f"  Parsed event for user: {event.get('user')}")

                            except json.JSONDecodeError as je:
                                print(f"  Failed to parse JSON: {je}")
                                continue

                except Exception as e:
                    print(f"  Error processing signature: {e}")
                    continue
            print(f"  Retrieved {len(events)} audit events from blockchain\n")
            return events

        except Exception as e:
            print(f"  Blockchain query failed: {e}")
            print(f"  Falling back to local file...")

            # Fallback to local file
            if not os.path.exists(self.local_log_file):
                return []

            with open(self.local_log_file, 'r') as f:
                return json.load(f)

    def _save_test_events(self):
        """Create test events for demonstration"""
        test_events = [
            {
                "user": "ssharkey",
                "action": "login",
                "result": "success",
                "timestamp": "2026-02-23T08:15:00",
                "source_ip": "192.168.10.107",
                "risk_score": 10
            },
            {
                "user": "ghouse",
                "action": "login",
                "result": "failed",
                "timestamp": "2026-02-23T08:16:30",
                "source_ip": "192.168.10.108",
                "risk_score": 45
            },
            {
                "user": "ghouse",
                "action": "login",
                "result": "failed",
                "timestamp": "2026-02-23T08:17:15",
                "source_ip": "192.168.10.108",
                "risk_score": 65
            },
            {
                "user": "ghouse",
                "action": "login",
                "result": "success",
                "timestamp": "2026-02-23T08:18:00",
                "source_ip": "192.168.10.108",
                "risk_score": 20
            },
            {
                "user": "mratched",
                "action": "login",
                "result": "success",
                "timestamp": "2026-02-23T08:20:00",
                "source_ip": "192.168.10.109",
                "risk_score": 5
            },
            {
                "user": "wbreen",
                "action": "admin_access",
                "result": "success",
                "timestamp": "2026-02-23T14:30:00",
                "source_ip": "192.168.10.100",
                "risk_score": 15
            },
            {
                "user": "unknown",
                "action": "login",
                "result": "failed",
                "timestamp": "2026-02-23T23:45:00",
                "source_ip": "192.168.10.200",
                "risk_score": 95
            },
        ]

        os.makedirs(LOG_DIR, exist_ok=True)
        with open(self.local_log_file, 'w') as f:
            json.dump(test_events, f, indent=2)

        print(f" Created {len(test_events)} test events\n")

if __name__ == "__main__":
    print("=== Audit Trail Query Tool ===\n")

    # Initialise
    query = AuditQuery()

    # Create test data
    query._save_test_events()

    # Test 1: Query by user
    query.query_by_user("ssharkey")

    print("\n" + "="*70 + "\n")

    # Test 2: Failed logins
    query.query_failed_logins(threshold=2)

    print("\n" + "="*70 + "\n")

    # Test 3: High-risk events
    query.query_high_risk_events(risk_threshold=60)
    
    print("\n" + "="*70 + "\n")

    # Test 4: Timeline
    query.generate_timeline()

    print("\n=== Query Complete ===")