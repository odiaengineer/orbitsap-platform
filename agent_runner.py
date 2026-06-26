import pyrfc
import requests
import time
from datetime import datetime

# Platform connection
PLATFORM_URL = "http://localhost:8000"
API_KEY = "79863c05f0ed26ec914d99900912e2dee2b8d3615e0f3fa8f495d3fcd5b3cda7"
AGENT_ID = 1

# SAP connection
SAP_CONFIG = {
    'ashost': 'bestehp',
    'sysnr': '67',
    'client': '000',
    'user': 'DDIC',
    'passwd': 'Welcome123'
}

HEADERS = {"api-key": API_KEY}

def sap_connect():
    return pyrfc.Connection(**SAP_CONFIG)

def report_step(run_id, step_name, status, message=None):
    requests.post(
        f"{PLATFORM_URL}/api/runs/{run_id}/steps",
        params={"step_name": step_name, "status": status, "message": message},
        headers=HEADERS
    )
    print(f"[{status.upper()}] {step_name}: {message or ''}")

def step_get_system_info(conn, run_id):
    result = conn.call('RFC_SYSTEM_INFO')
    info = result['RFCSI_EXPORT']
    msg = f"SID={info['RFCSYSID']} Host={info['RFCHOST']} Release={info['RFCSAPRL']}"
    report_step(run_id, "get_system_info", "success", msg)
    return info

def step_lock_users(conn, run_id):
    try:
        result = conn.call('RFC_READ_TABLE',
            QUERY_TABLE='USR02',
            FIELDS=[{'FIELDNAME': 'BNAME'}, {'FIELDNAME': 'UFLAG'}],
            ROWCOUNT=10
        )
        count = len(result['DATA'])
        report_step(run_id, "lock_users", "success", f"Found {count} users in system")
    except Exception as e:
        report_step(run_id, "lock_users", "error", str(e))

def step_check_interfaces(conn, run_id):
    try:
        result = conn.call('RFC_READ_TABLE',
            QUERY_TABLE='RFCDES',
            FIELDS=[{'FIELDNAME': 'RFCDEST'}, {'FIELDNAME': 'RFCTYPE'}],
            ROWCOUNT=10
        )
        count = len(result['DATA'])
        report_step(run_id, "check_interfaces", "success", f"Found {count} RFC destinations")
    except Exception as e:
        report_step(run_id, "check_interfaces", "error", str(e))

def step_check_clients(conn, run_id):
    try:
        result = conn.call('RFC_READ_TABLE',
            QUERY_TABLE='T000',
            FIELDS=[{'FIELDNAME': 'MANDT'}, {'FIELDNAME': 'MTEXT'}],
            ROWCOUNT=10
        )
        clients = [row['WA'].strip() for row in result['DATA']]
        report_step(run_id, "check_clients", "success", f"Clients: {clients}")
    except Exception as e:
        report_step(run_id, "check_clients", "error", str(e))

def run_post_refresh(run_id):
    print(f"\n{'='*50}")
    print(f"OrbitSAP - Starting Post Refresh Run #{run_id}")
    print(f"Time: {datetime.utcnow().isoformat()}")
    print(f"{'='*50}\n")

    conn = sap_connect()
    print("Connected to SAP DPK\n")

    step_get_system_info(conn, run_id)
    step_lock_users(conn, run_id)
    step_check_interfaces(conn, run_id)
    step_check_clients(conn, run_id)

    conn.close()

    requests.post(
        f"{PLATFORM_URL}/api/runs/{run_id}/complete",
        params={"status": "completed"},
        headers=HEADERS
    )

    print(f"\n{'='*50}")
    print(f"Refresh Run #{run_id} Completed Successfully")
    print(f"{'='*50}\n")

if __name__ == '__main__':
    run_post_refresh(1)
