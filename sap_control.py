import subprocess
import requests
import time
from datetime import datetime
from app.core.config import SAP_SIDADM, SAP_HOST, SAP_SYSNR, PLATFORM_URL, API_KEY

HEADERS = {"api-key": API_KEY}

def ssh_run(command):
    result = subprocess.run(
        ['ssh', f'{SAP_SIDADM}@{SAP_HOST}', command],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=120
    )
    return result.stdout.decode().strip(), result.stderr.decode().strip(), result.returncode

def report_step(run_id, step_name, status, message=None):
    requests.post(
        f"{PLATFORM_URL}/api/runs/{run_id}/steps",
        params={"step_name": step_name, "status": status, "message": message},
        headers=HEADERS
    )
    icon = "✓" if status == "success" else "✗"
    print(f"  [{icon}] {step_name}: {message or ''}")

def step_sap_status(run_id):
    out, err, rc = ssh_run(f"sapcontrol -nr {SAP_SYSNR} -function GetProcessList")
    if rc == 0 or rc == 3:
        report_step(run_id, "sap_status_check", "success", out[:300])
    else:
        report_step(run_id, "sap_status_check", "error", err[:200])

def step_sap_stop(run_id):
    out, err, rc = ssh_run(f"sapcontrol -nr {SAP_SYSNR} -function Stop")
    if "OK" in out or rc == 0:
        report_step(run_id, "sap_stop", "success", "SAP stop command issued")
        time.sleep(30)
    else:
        report_step(run_id, "sap_stop", "error", f"Stop failed: {err[:200]}")

def step_wait_stopped(run_id):
    for i in range(30):
        out, err, rc = ssh_run(f"sapcontrol -nr {SAP_SYSNR} -function GetProcessList")
        if rc == 4:
            report_step(run_id, "sap_wait_stopped", "success", "SAP stopped completely")
            return True
        print(f"  Still stopping... ({(i+1)*10}s)")
        time.sleep(10)
    report_step(run_id, "sap_wait_stopped", "error", "Timeout")
    return False

def step_sap_start(run_id):
    out, err, rc = ssh_run(f"sapcontrol -nr {SAP_SYSNR} -function Start")
    if "OK" in out or rc == 0:
        report_step(run_id, "sap_start", "success", "SAP start command issued")
        time.sleep(30)
    else:
        report_step(run_id, "sap_start", "error", f"Start failed: {err[:200]}")

def step_wait_started(run_id):
    for i in range(30):
        out, err, rc = ssh_run(f"sapcontrol -nr {SAP_SYSNR} -function GetProcessList")
        if rc == 0:
            report_step(run_id, "sap_wait_started", "success", "SAP started — all processes GREEN")
            return True
        print(f"  Still starting... ({(i+1)*10}s)")
        time.sleep(10)
    report_step(run_id, "sap_wait_started", "error", "Timeout")
    return False

def run_stop_start(run_id):
    print(f"\n{'='*50}")
    print(f"OrbitSAP — SAP Stop/Start Run #{run_id}")
    print(f"{'='*50}\n")
    step_sap_status(run_id)
    step_sap_stop(run_id)
    step_wait_stopped(run_id)
    step_sap_start(run_id)
    step_wait_started(run_id)
    requests.post(
        f"{PLATFORM_URL}/api/runs/{run_id}/complete",
        params={"status": "completed"},
        headers=HEADERS
    )
    print(f"\n>>> Run #{run_id} completed")

if __name__ == '__main__':
    run_id = int(input("Enter Run ID: "))
    run_stop_start(run_id)
