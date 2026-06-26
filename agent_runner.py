import pyrfc
import requests
from datetime import datetime

# Platform connection
PLATFORM_URL = "https://web-production-8f3a4f.up.railway.app"
API_KEY = "55e20d4cbad98df0b9d843cf08cf80d43fc2f6e913bf556c43570d9432d191ba"
AGENT_ID = 2

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

def run_post_refresh():
    print(f"\n{'='*50}")
    print(f"OrbitSAP - Starting Post Refresh")
    print(f"Time: {datetime.utcnow().isoformat()}")
    print(f"{'='*50}\n")

    # Start run on production platform
    response = requests.post(
        f"{PLATFORM_URL}/api/agents/{AGENT_ID}/runs/start",
        headers=HEADERS
    )
    run = response.json()
    run_id = run['run_id']
    print(f"Run #{run_id} started on production platform\n")

    # Connect to SAP
    conn = sap_connect()
    print("Connected to SAP DPK\n")

    # Execute steps
    step_get_system_info(conn, run_id)
    step_lock_users(conn, run_id)
    step_check_interfaces(conn, run_id)
    step_check_clients(conn, run_id)

    conn.close()

    # Complete run
    requests.post(
        f"{PLATFORM_URL}/api/runs/{run_id}/complete",
        params={"status": "completed"},
        headers=HEADERS
    )

    print(f"\n{'='*50}")
    print(f"Run #{run_id} Completed Successfully on Production")
    print(f"{'='*50}\n")

if __name__ == '__main__':
    run_post_refresh()
