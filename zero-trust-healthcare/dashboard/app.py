#!/usr/bin/env python3
"""
Zero Trust Healthcare Network Dashboard
Real time monitoring and visualisation
"""

from flask import Flask, render_template, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

# Configuration
BLOCKCHAIN_SCRIPTS_DIR = "home/jaboris/final-year-project/zero-trust-healthcare/blockchain-scripts"
LOG_DIR = os.path.join(BLOCKCHAIN_SCRIPTS_DIR, "logs")
BACKUP_DIR = os.path.join(BLOCKCHAIN_SCRIPTS_DIR, "backups")

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/network-status')
def network_status():
    """Get network and VLAN status"""
    return jsonify({
        "timestamp": datetime.now().isoformat(),
        "vlans": [
            {
                "name": "Clinical",
                "subnet": "192.168.10.0/24",
                "gateway": "192.168.10.1",
                "status": "active",
                "devices": 3
            },
            {
                "name": "Admins",
                "subnet": "192.168.20.0/24",
                "gateway": "192.168.20.1",
                "status": "active",
                "devices": 2
            },
            {
                "name": "IoT",
                "subnet": "192.168.30.0/24",
                "gateway": "192.168.30.1",
                "status": "active",
                "devices": 3
            },
            {
                "name": "Data",
                "subnet": "192.168.40.0/24",
                "gateway": "192.168.40.1",
                "status": "active",
                "devices": 2
            },
        ],
        "firewall_rules": {
            "total": 4,
            "active": 4,
            "blocked_today": 127
        }
    })

@app.route('/api/auth-events')
def auth_events():
    """Get recent authentication events"""
    log_file = os.path.join(LOG_DIR, "audit_events.json")

    if not os.path.exists(log_file):
        return jsonify([])

    try:
        with open(log_file, 'r') as f:
            events = json.load(f)

        # Return last 10 events
        return jsonify(events[-10:])
    except:
        return jsonify([])

@app.route('/api/backup-status')
def backup_status():
    """Get backup verification status"""
    records_file = os.path.join(BACKUP_DIR, "backup_records.json")

    if not os.path.exists(records_file):
        return jsonify({
            "total_backups": 0,
            "verified": 0,
            "last_backup": None
        })

    try:
        with open(records_file, 'r') as f:
            records = json.load(f)

        return jonify({
            "total_backups": len(records),
            "verified": len(records),
            "last_backup": max([r["timestamp"] for r in records.values()]) if records else None,
            "backups": list(records.values())[-5:] # Last 5 backups
        })
    except:
        return jsonify({
            "total_backups": 0,
            "verified": 0,
            "last_backup": None
        })

@app.route('/api/securiy-metrics')
def security_metric():
    """Get security and attack metrics:"""
    return jsonify({
        "timestamp": datetime.now().isoformat(),
        "metrics": {
            "containment_effectiveness": 91.7,
            "lateral_movement_blocked": 100,
            "detection_time_seconds": 45,
            "systems_compromise": 1,
            "systems_protected": 11,
            "backup_integrity": 100
        },
        "recent_attacks": [
            {
                "type": "LYNX Ransomware Simulation",
                "timestamp": "2026-02-27T09:15:00",
                "status": "Contained",
                "affected_vlan": "Clinical"
            }
        ]
    })

    @app.route('/api/blockchain-stats')
    def blockchain_stats():
        """Get blockchain audit statistics"""
        return jsonify({
            "wallet_address": "5ke13HRGtHi5TMbqC8JYYxympEmAwDJSpwEtePgAYxWG",
            "network": "devnet",
            "status": "simulated",
            "total_transactions": 247,
            "audit_events_logged": 234,
            "backup_hashes_stored": 13,
            "immutability": "100%"
        })

    if __name__ == '__main__':
        print("="*60)
        print("Zero Trust Healthcare Network Dashboard")
        print("="*60)
        print(f"\nStarting server at http://127.0.0.1:5000")
        print("Press Ctrl+C to stop\n")

        app.run(debug=True, host='0.0.0.0', port=5000)
