#!/usr/bin/env python3
"""
Backup Hash Verification with Solana Blockchain
Stores backup file hashes on blockchain for integrity verification
"""

from solana.rpc.api import Client
from solders.keypair import Keypair
import json
import hashlib
from datetime import datetime
import os

# Configuration
SOLANA_DEVNET_URL = "https://api.devnet.solana.com"
WALLET_PATH = "/home/jaboris/final-year-project/zero-trust-healthcare/blockchain-scripts/keys/audit-wallet.json"
BACKUP_DIR = "/home/jaboris/final-year-project/zero-trust-healthcare/blockchain-scripts/backups"

class BackupVerifier:
    def __init__(self):
        """Initialise Solana connection and wallet"""
        self.client = Client(SOLANA_DEVNET_URL)

        # lOAD WALLET KEYPAIR
        with open(WALLET_PATH, 'r') as f:
            secret_key = json.load(f)
        self.keypair = Keypair.from_bytes(bytes(secret_key))

        print(f"Backup Verifier initialised")
        print(f"Wallet: {self.keypair.pubkey()}")

    def calculate_hash(self, filepath):
        """Calculate SHA-256 hash of a file"""
        sha256_hash = hashlib.sha256()

        try:
            with open(filepath, "rb") as f:
                # Read file in chunks to handle large files
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)

            file_hash = sha256_hash.hexdigest()
            print(f" Hash calculated: {file_hash[:16]}...")
            return file_hash

        except FileNotFoundError:
            print(f" Error: File not found: {filepath}")
            return None
        except Exception as e:
            print(f" Error calculating hash: {e}")
            return None

    def store_backup_hash(self, backup_name, filepath):
        """
        Calculate hash and store on blockchain
        """
        print(f"\n--- Storing Backup Hash")
        print(f"Backup: {backup_name}")
        print(f"File: {filepath}")

        # Calculate hash
        file_hash = self.calculate_hash(filepath)
        if not file_hash:
            return {"status": "error", "message": "Hash calculation failed"}

        # Get file metadata
        file_size = os.path.getsize(filepath)
        timestamp = datetime.now().isoformat()

        # Create backup record
        backup_record = {
            "backup_name": backup_name,
            "filepath": filepath,
            "hash": file_hash,
            "size_bytes": file_size,
            "timestamp": timestamp
        }

        # Log to blockchain (simulated for now)
        print(f"\n[BLOCKCHAIN] Would store:")
        print(f"  Backup: {backup_name}")
        print(f"  Hash: {file_hash}")
        print(f"  Size: {file_size} bytes")
        print(f"  Time: {timestamp}")

        # Save locally as well
        self._save_local_record(backup_record)

        return {"status": "simulated", "hash": file_hash, "record": backup_record}

    def verify_backup_integrity(self, backup_name, filepath):
        """
        Verify backup hasn't been tampered with
        Compare current hash with blockchain stored hash
        """
        print(f"\n--- Verifying Backup Integrity ---")
        print(f"Backup: {backup_name}")

        # Calculate current has
        current_hash = self.calculate_hash(filepath)
        if not current_hash:
            return {"status": "error", "message": "Cannot calculate current hash"}

        # Get stored hash (from local records for now)
        stored_record = self._get_local_record(backup_name)

        if not stored_record:
            print(f"\nCurrent hash found for {backup_name}")
            return {"status": "error", "message": "No stored hash found"}

        stored_hash = stored_record.get("hash")

        # Compare hashes
        print(f"\nCurent hash: {current_hash}")
        print(f"Store hash: {stored_hash}")

        if current_hash == stored_hash:
            print(f" VERIFIED: Backup is intact and unmodified")
            return {
                "status": "verified",
                "match": True,
                "backup_name": backup_name,
                "timestamp": stored_record.get("timestamp")
            }
        else:
            print(f" WARNING: Hash mismatch! Backup may be compromised!")
            return {
                "status": "failed",
                "match": False,
                "backup_name": backup_name
            }

    def _save_local_record(self, record):
        """Save backup record locally (temporary until blockchain works)"""
        records_file = os.path.join(BACKUP_DIR, "backup_record.json")

        # Load existing records
        if os.path.exists(records_file):
            with open(records_file, 'r') as f:
                records = json.load(f)
        else:
            records = {}

        # Add new record
        record[record["backup_name"]] = record

        # Save
        os.makedirs(BACKUP_DIR, exist_ok=True)
        with open (records_file, 'w') as f:
            json.dump(records, f, indent=2)

        print(f" Record saved locally")

    def _get_local_record(self, backup_name):
        """Retrieve stored backup record"""
        records_file = os.path.join(BACKUP_DIR, "backup_records.json")

        if not os.path.exists(records_file):
            return None

        with open(records_file, 'r') as f:
            records = json.load(f)

        return records.get(backup_name)

if __name__ == "__main__":
    print("=== Backup Hash Verifier Test ===\n")

    # Initialise verifier
    verifier = BackupVerifier()

    # Create a test backup file
    test_backup_path = os.path.join(BACKUP_DIR, "test_backup.txt")
    os.makedirs(BACKUP_DIR, exist_ok=True)

    with open(test_backup_path, 'w') as f:
        f.write("This is a test backup file for the healthcare network.\n")
        f.write("Patient data would be encrypted here.\n")
        f.write(f"Backup created: {datetime.now()}\n")

    print(f"Created test backup: {test_backup_path}\n")

    # Test 1: Store backup hash
    result1 = verifier.store_backup_hash("ehr_backup_2026_02_23", test_backup_path)

    # Test 2: Verify backup (should match)
    result2 = verifier.verify_backup_integrity("ehr_backup_2026_02_23", test_backup_path)

    #Test 3: Modify backup and verify (should fail)
    print("\n\n--- Test: Detecting Tampering ---")
    with open(test_backup_path, 'a') as f:
        f.write("TAMPERED DATA!\n")

    result3 = verifier.verify_backup_integrity("ehr_backup_2026_02_23", test_backup_path)
    
    print("\n=== Test Complete ===")



