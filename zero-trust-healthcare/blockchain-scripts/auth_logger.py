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
SOLANA_DEVNET_URL = "http://localhost:8899"
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
            'user': 'ssharkey',
            'action': 'login',
            'result': 'success',
            'timestamp': '2026-02-22T12:00:00Z',
            'source_ip': '192.168.10.107'
            'risk_score': 15
        }
        """
        try:
            from solders.transaction import Transaction
            from solders.message import Message
            from solders.instruction import Instruction, AccountMeta
            from solders.pubkey import Pubkey
            from solders.system_program import ID as SYS_PROGRAM_ID
            
            # Convert event to JSON string for memo
            event_json = json.dumps(event_data)

            # Create memo instruction (stores audit data on-chain)
            MEMO_PROGRAM_ID = Pubkey.from_string("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr")
            memo_ix = Instruction(
                program_id=MEMO_PROGRAM_ID,
                accounts=[],
                data=event_json.encode('utf-8')
            )

            # Get recent blockhash
            recent_blockhash = self.client.get_latest_blockhash().value.blockhash

            # Create transaction
            message = Message.new_with_blockhash(
                [memo_ix],
                self.keypair.pubkey(),
                recent_blockhash
            )
            
            txn = Transaction([self.keypair], message, recent_blockhash)

            # Send transaction
            print(f"\n[BLOCKCHAIN] Submitting audit log transaction...")
            print(f"  Event: {event_json}")

            response = self.client.send_transaction(txn)
            signature = str(response.value)

            print(f"  Transaction confirmed!")
            print(f"  Signature: {signature}")
            print(f"  Explorer: htt[://localhost:8899/tx/{signature}]")

            return {
                "status": "success",
                "signature": signature,
                "event": event_data,
                "timestamp": datetime.now().isoformat()
                }

        except Exception as e:
            print(f"  Error logging event: {e}")
            print(f"  Falling back to local storage...")

            # Fallback: save locally if blockchain fails
            self._save_local(event_data)

            return {"status": "error", "message": str(e)}

    def _save_local(self, event_data):
        """Save event locally if blockchain transaction fails"""
        filename = "audit_log_local.json"

        try:
            # Load existing data
            try:
                with open(filename, 'r') as f:
                    log_data = json.load(f)
            except FileNotFoundError:
                log_data = []

            # Append new event
            log_data.append(event_data)

            # Save back
            with open(filename, 'w') as f:
                json.dump(log_data, f, indent=2, default=str)

            print(f"    Saved locally to {filename}")

        except Exception as e:
            print(f"  Local save also failed: {e}")

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
    