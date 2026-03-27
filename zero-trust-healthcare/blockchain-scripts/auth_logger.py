#!/usr/bin/env python3
"""
Authentication Event Logger to Solana Blockchain
Logs pfSense/AD authentication attempts with immutable timestamps
"""

from solana.rpc.api import Client 
from solders.keypair import Keypair
from solders.transaction import Transaction
from solders.system_program import TransferParams, transfer 
from solders.pubkey import Pubkey
import json
from datetime import datetime
import os

# Configuration
SOLANA_DEVNET_URL = "https://localhost:8899"
WALLET_PATH = "/home/jaboris/Documents/GitHub/Final-Year-Project/zero-trust-healthcare/blockchain-scripts/keys/audit-wallet.json"

class AuthLogger:
    def __init__(self):
        """Initialize Solana connection and wallet"""
        self.client = Client(SOLANA_DEVNET_URL)

        # Load wallet keypair 
        with open(WALLET_PATH, 'r') as f:
            secret_key = json.load(f)
        self.keypair = Keypair.from_bytes(bytes(secret_key))

        print(f"Connected to Solana devnet")
        print(f"Wallet address: {self.keypair.pubkey()}")

    def log_auth_event(self, event_data):
        """
        Log authentication event to blockchain
        event_data = {
            'user': 'jdoe',
            'action': 'login',
            'result': 'success',
            'timestamp': '2026-02-22T12:00:00Z',
            'source_ip': '192.168.10.107'
            'risk_score': 15
        }
        """
        try:
            # Convert event to JSON string for memo
            event_json = json.dumps(event_data)

            # Create transaction with memo (event data sotred in memo field)
            # For now, just print - actual transaction needs SOL
            print(f"\n[AUDIT LOG] Would log to blockchain:")
            print(f"  Event: {event_json}")
            print(f"  Wallet: {self.keypair.pubkey()}")
            print(f"  Timestamp: {datetime.now().isoformat()}")

            # When you have SOL, uncomment this to actually send:
            # txn = Transaction()
            # ... add memo instruction ...
            # response = self.client.send_transaction(txn, self.keypair)

            return {"status": "simulated", "event": event_data}

        except Exception as e:
            print(f"Error logging event: {e}")
            return {"status": "error", "message": str(e)}

    def query_audit_trail(self, user=None, start_date=None):
        """Query blockchain for audit events"""
        print(f"\n[QUERY] Searching audit trail...")
        print(f"  User filter: {user}")
        print(f"  Start date: {start_date}")
        print(f"  Note: Full implementation requires parsing transaction history")

        # This would query blockchain transactions
        # For now return simulated data
        return[]

if __name__ == "__main__":
    print("=== Authentication Logger Test ===\n")

    # Initialise logger
    logger = AuthLogger()
    
    # Test event 1: Successful login
    test_event1 = {
        'user': 'ssharkey',
        'action': 'login',
        'result': 'success',
        'timestamp': datetime.now().isoformat(),
        'source_ip': '192.168.10.107',
        'risk_score': 10
    }
    result1 = logger.log_auth_event(test_event1)

    # Test event 2: Failed login
    test_event2 = {
        'user': 'ghouse',
        'action': 'login',
        'result': 'failed',
        'timestamp': datetime.now().isoformat(),
        'source_ip': '192.168.10.108',
        'risk_score': 75
    }
    result2 = logger.log_auth_event(test_event2)

    # Test query
    logger.query_audit_trail(user='ssharkey')

    print("\n=== Test Complete ===")
    