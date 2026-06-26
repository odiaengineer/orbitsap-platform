from dotenv import load_dotenv
import os

load_dotenv()

SAP_HOST = os.getenv("SAP_HOST", "bestehp")
SAP_SYSNR = os.getenv("SAP_SYSNR", "67")
SAP_CLIENT = os.getenv("SAP_CLIENT", "000")
SAP_USER = os.getenv("SAP_USER")
SAP_PASSWORD = os.getenv("SAP_PASSWORD")
SAP_SIDADM = os.getenv("SAP_SIDADM", "dpkadm")
PLATFORM_URL = os.getenv("PLATFORM_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY")
AGENT_ID = int(os.getenv("AGENT_ID", "1"))
SECRET_KEY = os.getenv("SECRET_KEY", "changeme")
