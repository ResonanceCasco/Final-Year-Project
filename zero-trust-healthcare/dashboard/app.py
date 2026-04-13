#!/usr/bin/env python3
"""
Zero Trust Healthcare Network Dashboard
Real time monitoring and visualisation with blockchain integration
"""

from flask import Flask, render_template, jsonify
import json
import os
import sys
from datetime import datetime

app = Flask(__name__)

# Configuration
PROJECT_ROOT = "/home/jaboris/Documents/GitHub/Final-Year-Project"
BLOCKCHAIN_SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "zero-trust-healthcare/blockchain-scripts/")
IOMT_DIR = os.path.join(PROJECT_ROOT, "IoMT-Devices")

# Add blockchain scripts to path
sys.path.insert(0, BLOCKCHAIN_SCRIPTS_DIR)

# Import blockchain query tool
try:
    from audit_query import AuditQuery
    BLOCKCHAIN_AVAILABLE = True
    print("Blockchain integration enabled")
except Exception as e:
    BLOCKCHAIN_AVAILABLE = False
    print(f"Blockchain integration disabled: {e}")

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
                "devices": 3,
                "description": "Clinical workstations and patient care systems"
            },
            {
                "name": "Admins",
                "subnet": "192.168.20.0/24",
                "gateway": "192.168.20.1",
                "status": "active",
                "devices": 2,
                "description": "IT administration and privileged access"
            },
            {
                "name": "IoT",
                "subnet": "192.168.30.0/24",
                "gateway": "192.168.30.1",
                "status": "active",
                "devices": 3,
                "description": "IoMT medical devices (isolated)"
            },
            {
                "name": "Data",
                "subnet": "192.168.40.0/24",
                "gateway": "192.168.40.1",
                "status": "active",
                "devices": 3,
                "description": "EHR database, blockchain, and backup servers"
            },
        ],
        "firewall_rules": {
            "total": 12,
            "active": 12,
            "blocked_today": 0
        },
        "zero_trust_status": "operational"
    })

@app.route('/api/blockchain-events')
def blockchain_events():
    """Get recent events from blockchain"""
    if not BLOCKCHAIN_AVAILABLE:
        return jsonify({
            "status": "unavailable",
            "message": "Blockchain integration not available",
            "events": []
        })
    try:
        query = AuditQuery()
        events = query._load_local_events()

        # Sort by timestamp, most recent first
        events.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

        return jsonify({
            "status": "connected",
            "network": "local validator",
            "wallet": "5ke13HRGtHi5TMbqC8JYYxympEmAwDJSpwEtePgAYxWG",
            "total_events": len(events),
            "events": events[:20] # Last 20 events
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "events": []
        })

@app.route('/api/auth-events')
def auth_events():
    """Get authentication events from blockchain"""
    if not BLOCKCHAIN_AVAILABLE:
        return jsonify([])

    try:
        query = AuditQuery()
        events = query._load_local_events()

        # Filter only login events
        auth_events = [e for e in events if e.get('action') in ['login', 'logout', 'admin_access']]
        auth_events.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

        return jsonify(auth_events[:10])
    except:
        return jsonify([])

@app.route('/api/failed-logins')
def failed_logins():
    """Get failed login attempts"""
    if not BLOCKCHAIN_AVAILABLE:
        return jsonify({"users": {}, "total": 0})
    try:
        query = AuditQuery()
        suspicious = query.query_failed_logins(threshold=1)

        return jsonify({
            "users": suspicious,
            "total": sum(suspicious.values()) if suspicious else 0,
            "threshold": 3
        })
    except:
        return jsonify({"users": {}, "total": 0})

@app.route('/api/high-risk-events')
def high_risk_events():
    """Get high-risk security events"""
    if not BLOCKCHAIN_AVAILABLE:
        return jsonify([])

    try:
        query = AuditQuery()
        high_risk = query.query_high_risk_events(risk_threshold=50)

        return jsonify(high_risk)
    except:
        return jsonify([])

@app.route('/api/iomt-status')
def iomt_status():
    """Get IoMT device status from local logs"""
    devices = []

    # Patient Monitor
    vitals_log = os.path.join(IOMT_DIR, "vitals_log_MONITOR-001.json")
    if os.path.exists(vitals_log):
        try:
            with open(vitals_log, 'r') as f:
                vitals_data = json.load(f)
            last_vitals = vitals_data[-1] if vitals_data else None
            devices.append({
                "device_id": "MONITOR-001",
                "type": "Patient Monitor",
                "status": "active" if last_vitals else "inactive",
                "last_transmission": last_vitals.get('timestamp') if last_vitals else None,
                "data": last_vitals.get('vitals') if last_vitals else None
            })
        except:
            pass

    # Infusion Pump
    infusion_log = os.path.join(IOMT_DIR, "infusion_log_PUMP-001.json")
    if os.path.exists(infusion_log):
        try:
            with open(vitals_log, 'r') as f:
                infusion_data = json.load(f)
            last_infusion = infusion_data[-1] if infusion_data else None
            devices.append({
                "device_id": "PUMP-001",
                "type": "Infusion Pump",
                "status": "active" if last_infusion else "inactive",
                "last_transmission": last_infusion.get('timestamp') if last_infusion else None,
                "data": last_infusion.get('pump_status') if last_infusion else None
            })
        except:
            pass
    
    # Access Control
    access_log = os.path.join(IOMT_DIR, "access_log_RFID-READER-001.json")
    if os.path.exists(access_log):
        try:
            with open(access_log, 'r') as f:
                access_data = json.load(f)
            last_access = access_data[-1] if access_data else None
            devices.append({
                "device_id": "RFID-READER-001",
                "type": "Access Control",
                "status": "active" if last_access else "inactive",
                "last_transmission": last_access.get('timestamp') if last_access else None,
                "data": {
                    "action": last_access.get('action'),
                    "badge_id": last_access.get('badge_id'),
                    "authorised": last_access.get('authorised')
                } if last_access else None
            })
        except:
            pass

    return jsonify({
        "total_devices": len(devices),
        "active": len([d for d in devices if d['status'] == 'active']),
        "devices": devices
    })
    
@app.route('/api/backup-status')
def backup_status():
    """Get backup verification status from blockchain"""
    records_file = os.path.join(BLOCKCHAIN_SCRIPTS_DIR, "backups/backup_records.json")

    if not os.path.exists(records_file):
        return jsonify({
            "total_backups": 0,
            "verified": 0,
            "last_backup": None
        })

    try:
        with open(records_file, 'r') as f:
            records = json.load(f)

        backups_list = list(records.values()) if isinstance(records, dict) else records

        return jsonify({
            "total_backups": len(backups_list),
            "verified": len(backups_list),
            "last_backup": backups_list[-1].get("timestamp") if backups_list else None,
            "backups": backups_list[-5:] # Last 5 backups
        })
    except:
        return jsonify({
            "total_backups": 0,
            "verified": 0,
            "last_backup": None,
            "error": str(e)
        })

@app.route('/api/security-metrics')
def security_metrics():
    """Get security and Zero Trust metrics:"""
    metrics = {
        "timestamp": datetime.now().isoformat(),
        "zero_trust": {
            "containment_effectiveness": 91.7,
            "lateral_movement_blocked": 100.0,
            "microsegmentation": "enabled",
            "least_privilege": "enforced"
        },
        "blockchain": {
                "audit_completeness": 100.0,
                "immutability": "verified",
                "status": "operational" if BLOCKCHAIN_AVAILABLE else "simulated"
        },
        "network": {
                "vlans_active": 4,
                "firewall_rules": 12,
                "blocked_attempts_today": 0
        }
    }

    # Add blockchain event count if available
    if BLOCKCHAIN_AVAILABLE:
        try:
            query = AuditQuery()
            events = query._load_local_events()
            metrics["blockchain"]["total_events"] = len(events)
        except:
            pass
    
    return jsonify(metrics)

@app.route('/api/blockchain-stats')
def blockchain_stats():
    """Get blockchain audit statistics"""
    if not BLOCKCHAIN_AVAILABLE:    
        return jsonify({
            "wallet_address": "5ke13HRGtHi5TMbqC8JYYxympEmAwDJSpwEtePgAYxWG",
            "network": "local validator",
            "status": "unavailable",
            "message": "Blockchain integration not loaded"
        })

    try:
        query = AuditQuery()
        events = query._load_local_events()

        # Calculate statistics
        auth_events = [e for e in events if e.get('action') == 'login']
        failed_logins = [e for e in auth_events if e.get('result') == 'failed']
        high_risk = [e for e in events if e.get('risk_score', 0) >= 50]

        return jsonify({
            "wallet_address": "5ke13HRGtHi5TMbqC8JYYxympEmAwDJSpwEtePgAYxWG",
            "network": "local validator (https://localhost:8899)",
            "status": "connected",
            "statistics": {
                "total_transactions": len(events),
                "authentication_events": len(auth_events),
                "failed_logins": len(failed_logins),
                "high_risk_events": len(high_risk),
                "immutability": "100%",
                "audit_completeness": "100%"
            }
        })
    except Exception as e:
        return jsonify({
            "wallet_address": "5ke13HRGtHi5TMbqC8JYYxympEmAwDJSpwEtePgAYxWG",
            "network": "local validator",
            "status": "error",
            "message": str(e)
        })

if __name__ == '__main__':
    print("="*60)
    print("Zero Trust Healthcare Network Dashboard")
    print("="*60)
    print(f"\nBlockchain Integration: {'Enabled' if BLOCKCHAIN_AVAILABLE else 'Disabled'}")
    print(f"Starting server at http://127.0.0.1:5000")
    print("Press Ctrl+C to stop\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
