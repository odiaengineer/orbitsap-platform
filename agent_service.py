import pyrfc
import requests
import time
from datetime import datetime
from app.core.config import (
    SAP_HOST, SAP_SYSNR, SAP_CLIENT,
    SAP_USER, SAP_PASSWORD,
    PLATFORM_URL, API_KEY, AGENT_ID
)

SAP_CONFIG = {
    'ashost': SAP_HOST,
    'sysnr': SAP_SYSNR,
    'client': SAP_CLIENT,
    'user': SAP_USER,
    'passwd': SAP_PASSWORD
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
    icon = "✓" if status == "success" else "✗"
    print(f"  [{icon}] {step_name}: {message or ''}")

def step_export_rfc(conn, run_id):
    try:
        result = conn.call('RFC_READ_TABLE',
            QUERY_TABLE='RFCDES',
            FIELDS=[{'FIELDNAME': 'RFCDEST'}],
            ROWCOUNT=100
        )
        count = len(result['DATA'])
        destinations = [row['WA'].strip() for row in result['DATA'][:5]]
        report_step(run_id, "export_rfc_destinations", "success",
            f"Exported {count} RFC destinations. Sample: {', '.join(destinations)}")
    except Exception as e:
        report_step(run_id, "export_rfc_destinations", "error", str(e))

def step_stms_setup(conn, run_id):
    try:
        result = conn.call('RFC_READ_TABLE',
            QUERY_TABLE='TMSCSYS',
            FIELDS=[{'FIELDNAME': 'SYSNAM'}],
            ROWCOUNT=50
        )
        count = len(result['DATA'])
        systems = [row['WA'].strip() for row in result['DATA']]
        report_step(run_id, "stms_setup_verify", "success",
            f"TMS landscape has {count} systems: {', '.join(systems)}")
    except Exception as e:
        report_step(run_id, "stms_setup_verify", "error", str(e))

def step_bdls(conn, run_id):
    try:
        result = conn.call('RFC_READ_TABLE',
            QUERY_TABLE='TBDLS',
            FIELDS=[{'FIELDNAME': 'LOGSYS'}],
            ROWCOUNT=50
        )
        count = len(result['DATA'])
        systems = [row['WA'].strip() for row in result['DATA']]
        report_step(run_id, "bdls_logical_systems", "success",
            f"Found {count} logical systems: {', '.join(systems)}")
    except Exception as e:
        report_step(run_id, "bdls_logical_systems", "error", str(e))

def step_lock_users(conn, run_id):
    try:
        result = conn.call('RFC_READ_TABLE',
            QUERY_TABLE='USR02',
            FIELDS=[{'FIELDNAME': 'BNAME'}, {'FIELDNAME': 'UFLAG'}],
            ROWCOUNT=200
        )
        count = len(result['DATA'])
        report_step(run_id, "lock_all_users", "success",
            f"Identified {count} users to lock")
    except Exception as e:
        report_step(run_id, "lock_all_users", "error", str(e))

def step_system_info(conn, run_id):
    try:
        result = conn.call('RFC_SYSTEM_INFO')
        info = result['RFCSI_EXPORT']
        report_step(run_id, "system_info", "success",
            f"SID={info['RFCSYSID']} Release={info['RFCSAPRL']} Kernel={info['RFCKERNRL']}")
    except Exception as e:
        report_step(run_id, "system_info", "error", str(e))

def execute_run(run_id):
    print(f"\n{'='*50}")
    print(f"OrbitSAP — Executing Run #{run_id}")
    print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*50}")
    try:
        conn = sap_connect()
        print(f"Connected to SAP\n")
        step_system_info(conn, run_id)
        step_export_rfc(conn, run_id)
        step_stms_setup(conn, run_id)
        step_bdls(conn, run_id)
        step_lock_users(conn, run_id)
        conn.close()
        requests.post(
            f"{PLATFORM_URL}/api/runs/{run_id}/complete",
            params={"status": "completed"},
            headers=HEADERS
        )
        print(f"\n>>> Run #{run_id} completed successfully")
    except Exception as e:
        print(f">>> Run #{run_id} failed: {e}")
        requests.post(
            f"{PLATFORM_URL}/api/runs/{run_id}/complete",
            params={"status": "failed"},
            headers=HEADERS
        )

def poll():
    print("OrbitSAP Agent Service started")
    print(f"Platform: {PLATFORM_URL}")
    print(f"SAP Host: {SAP_HOST} / SID: *** / Instance: {SAP_SYSNR}")
    print(f"Agent ID: {AGENT_ID}\n")
    while True:
        try:
            res = requests.get(
                f"{PLATFORM_URL}/api/agents/{AGENT_ID}/runs",
                headers=HEADERS
            )
            runs = res.json()
            pending = [r for r in runs if r['status'] == 'pending']
            if pending:
                for run in pending:
                    execute_run(run['id'])
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Waiting...", end='\r')
        except Exception as e:
            print(f"Poll error: {e}")
        time.sleep(10)

if __name__ == '__main__':
    poll()
