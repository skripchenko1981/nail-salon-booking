"""Utility: delete TEST_ bookings/clients created by the QA suite."""
import os
import requests
from dotenv import dotenv_values

BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL")
            or dotenv_values("/app/frontend/.env").get("REACT_APP_BACKEND_URL")).rstrip("/")

s = requests.Session()
tok = s.post(f"{BASE_URL}/api/admin/login", json={"username": "admin", "password": "admin123"}).json()
tok = tok.get("token") or tok.get("access_token")
h = {"Authorization": f"Bearer {tok}"}
rows = s.get(f"{BASE_URL}/api/admin/bookings", headers=h).json()
n = 0
for b in rows:
    if str(b.get("client_name", "")).startswith("TEST_"):
        r = s.delete(f"{BASE_URL}/api/admin/bookings/{b['id']}", headers=h)
        print(b["id"], b.get("date"), b.get("time"), r.status_code)
        n += 1
print("deleted", n)
