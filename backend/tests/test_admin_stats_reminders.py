"""Tests for admin stats endpoints (flat field refactor) + reminder master-notification logic."""
import os
import re
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import pytz
import requests
from dotenv import dotenv_values

frontend_env = dotenv_values("/app/frontend/.env")
base_url = os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL")
if not base_url:
    raise RuntimeError("REACT_APP_BACKEND_URL missing")
BASE_URL = base_url.rstrip("/")
API = f"{BASE_URL}/api"

KYIV = pytz.timezone("Europe/Kyiv")
MONTH_NAMES = ["Січень", "Лютий", "Березень", "Квітень", "Травень", "Червень",
               "Липень", "Серпень", "Вересень", "Жовтень", "Листопад", "Грудень"]

SERVICE_ID = "28858083-039f-423c-861f-f3f98e09b894"
SERVICE_MASTER_ID = "197c3a5e-9fe0-4863-90ee-77aa0babd2c8"


def _creds():
    content = Path("/app/memory/test_credentials.md").read_text(encoding="utf-8")
    login = re.search(r"(?im)^\s*[-*]\s*Login:\s*(\S+)", content)
    pwd = re.search(r"(?im)^\s*[-*]\s*Password:\s*(\S+)", content)
    if not login or not pwd:
        pytest.skip("admin credentials not found in test_credentials.md")
    return login.group(1), pwd.group(1)


@pytest.fixture(scope="session")
def admin_client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    user, pwd = _creds()
    r = s.post(f"{API}/admin/login", json={"username": user, "password": pwd})
    if r.status_code != 200:
        pytest.fail(f"Admin login failed: {r.status_code} {r.text[:300]}")
    token = r.json().get("token")
    assert token, "no token in admin login response"
    s.headers.update({"Authorization": f"Bearer {token}"})
    return s


@pytest.fixture(scope="session")
def all_bookings(admin_client):
    r = admin_client.get(f"{API}/admin/bookings")
    assert r.status_code == 200, r.text[:300]
    return r.json()


# ============ /api/admin/stats ============
class TestAdminStats:
    def test_stats_fields_and_counts(self, admin_client, all_bookings):
        r = admin_client.get(f"{API}/admin/stats")
        assert r.status_code == 200, r.text[:300]
        d = r.json()
        for key in ["total_bookings", "pending_bookings", "confirmed_bookings",
                    "completed_bookings", "cancelled_bookings", "today_bookings",
                    "total_revenue", "total_clients"]:
            assert key in d, f"missing {key}"
            assert isinstance(d[key], (int, float)), f"{key} not numeric: {d[key]}"

        assert d["total_bookings"] == len(all_bookings)
        for status, field in [("pending", "pending_bookings"), ("confirmed", "confirmed_bookings"),
                              ("completed", "completed_bookings"), ("cancelled", "cancelled_bookings")]:
            expected = len([b for b in all_bookings if b.get("status") == status])
            assert d[field] == expected, f"{field}={d[field]} expected {expected}"

        today = datetime.now(timezone.utc).astimezone(KYIV).strftime("%Y-%m-%d")
        assert d["today_bookings"] == len([b for b in all_bookings if b.get("date") == today])

        expected_rev = sum(b.get("price", 0) or 0 for b in all_bookings
                           if b.get("status") in ("confirmed", "completed"))
        assert d["total_revenue"] == expected_rev

    def test_stats_requires_auth(self):
        r = requests.get(f"{API}/admin/stats")
        assert r.status_code in (401, 403), r.status_code


# ============ /api/admin/stats/masters ============
class TestMastersStats:
    def test_masters_stats_flat_fields(self, admin_client, all_bookings):
        r = admin_client.get(f"{API}/admin/stats/masters")
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        assert isinstance(data, list) and len(data) > 0, "no masters stats returned"
        for m in data:
            for key in ["master_id", "master_name", "master_email", "is_active",
                        "total_bookings", "confirmed", "completed", "cancelled", "revenue"]:
                assert key in m, f"missing {key} in {m}"
            assert m["master_name"], "empty master_name"
            assert isinstance(m["total_bookings"], int)
            assert "_id" not in m and "password_hash" not in m

        # verify against actual bookings for each master
        for m in data:
            mb = [b for b in all_bookings if b.get("master_id") == m["master_id"]]
            assert m["total_bookings"] == len(mb), f"{m['master_name']} total mismatch"
            assert m["confirmed"] == len([b for b in mb if b.get("status") == "confirmed"])
            assert m["completed"] == len([b for b in mb if b.get("status") == "completed"])
            assert m["cancelled"] == len([b for b in mb if b.get("status") == "cancelled"])
            assert m["revenue"] == sum(b.get("price", 0) or 0 for b in mb
                                       if b.get("status") in ("confirmed", "completed"))

    def test_masters_stats_admin_only(self):
        r = requests.get(f"{API}/admin/stats/masters")
        assert r.status_code in (401, 403)


# ============ /api/admin/stats/monthly ============
class TestMonthlyStats:
    def test_monthly_structure_and_values(self, admin_client, all_bookings):
        year = 2026
        r = admin_client.get(f"{API}/admin/stats/monthly", params={"year": year})
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        assert len(data) == 12, f"expected 12 months, got {len(data)}"
        for i, m in enumerate(data):
            assert m["month"] == i + 1
            assert m["month_name"] == MONTH_NAMES[i]
            for key in ["total_bookings", "confirmed", "completed", "cancelled", "revenue"]:
                assert key in m and isinstance(m[key], (int, float)), f"bad {key} in {m}"

        year_bookings = [b for b in all_bookings if str(b.get("date", "")).startswith(f"{year}-")]
        assert sum(m["total_bookings"] for m in data) == len(year_bookings)
        expected_rev = sum(b.get("price", 0) or 0 for b in year_bookings
                           if b.get("status") in ("confirmed", "completed"))
        assert sum(m["revenue"] for m in data) == expected_rev

    def test_monthly_master_filter(self, admin_client, all_bookings):
        year = 2026
        r = admin_client.get(f"{API}/admin/stats/monthly",
                             params={"year": year, "master_id": SERVICE_MASTER_ID})
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        mb = [b for b in all_bookings
              if b.get("master_id") == SERVICE_MASTER_ID and str(b.get("date", "")).startswith(f"{year}-")]
        assert sum(m["total_bookings"] for m in data) == len(mb)
        for i, m in enumerate(data):
            month_key = f"{year}-{i + 1:02d}"
            assert m["total_bookings"] == len([b for b in mb if str(b["date"]).startswith(month_key)])

    def test_monthly_missing_year_returns_422(self, admin_client):
        r = admin_client.get(f"{API}/admin/stats/monthly")
        assert r.status_code == 422, r.status_code


# ============ Reminder master-notification flow ============
class TestReminderMasterNotification:
    created = []

    def _mongo_booking(self, booking_id):
        from pymongo import MongoClient
        env = dotenv_values("/app/backend/.env")
        client = MongoClient(env["MONGO_URL"])
        doc = client[env["DB_NAME"]].bookings.find_one({"id": booking_id})
        client.close()
        return doc

    def test_reminder_sets_master_notified_flag(self, admin_client):
        now_kyiv = datetime.now(timezone.utc).astimezone(KYIV)
        target = now_kyiv + timedelta(minutes=55)
        if target.date() != now_kyiv.date():
            pytest.skip("crosses midnight in Kyiv; skip time-sensitive reminder test")

        # find a free minute-aligned slot on today's date
        booking_id = None
        for attempt in range(6):
            t = (target + timedelta(minutes=attempt)).strftime("%H:%M")
            payload = {
                "master_id": SERVICE_MASTER_ID,
                "service_id": SERVICE_ID,
                "client_name": "TEST_Reminder",
                "client_phone": f"+38050{random.randint(1000000, 9999999)}",
                "date": now_kyiv.strftime("%Y-%m-%d"),
                "time": t,
                "reminder_hours": 2,
                "notes": "TEST reminder flow",
            }
            r = requests.post(f"{API}/bookings", json=payload)
            if r.status_code == 200:
                booking_id = r.json()["id"]
                break
            assert r.status_code == 400, f"unexpected {r.status_code}: {r.text[:300]}"
        if not booking_id:
            pytest.skip("no free slot within the reminder window today")
        self.created.append(booking_id)

        r1 = admin_client.post(f"{API}/admin/send-reminders")
        assert r1.status_code == 200, r1.text[:300]
        assert r1.json().get("success") is True

        doc = self._mongo_booking(booking_id)
        assert doc is not None, "booking not persisted"
        assert doc.get("reminder_master_notified") is True, \
            f"reminder_master_notified not set: {doc.get('reminder_master_notified')}"
        assert doc.get("reminder_sent") is not True, "reminder_sent should stay False (client not subscribed)"

        # second trigger must not re-notify (flag already true, stays true, no error)
        r2 = admin_client.post(f"{API}/admin/send-reminders")
        assert r2.status_code == 200, r2.text[:300]
        doc2 = self._mongo_booking(booking_id)
        assert doc2.get("reminder_master_notified") is True

    def test_cleanup_created_bookings(self, admin_client):
        for bid in list(self.created):
            r = admin_client.delete(f"{API}/admin/bookings/{bid}")
            assert r.status_code in (200, 204, 404), r.text[:200]


# ============ Regression ============
class TestRegression:
    def test_create_and_cancel_booking(self, admin_client):
        future = (datetime.now(timezone.utc).astimezone(KYIV) + timedelta(days=45)).strftime("%Y-%m-%d")
        payload = {
            "master_id": SERVICE_MASTER_ID,
            "service_id": SERVICE_ID,
            "client_name": "TEST_Regression",
            "client_phone": f"+38050{random.randint(1000000, 9999999)}",
            "date": future,
            "time": "11:00",
            "reminder_hours": 2,
        }
        r = requests.post(f"{API}/bookings", json=payload)
        assert r.status_code == 200, f"{r.status_code}: {r.text[:300]}"
        data = r.json()
        assert data.get("id") and data.get("status") == "pending"
        assert data.get("service_name")
        bid = data["id"]

        g = requests.get(f"{API}/bookings/{bid}")
        assert g.status_code == 200 and g.json()["date"] == future

        c = requests.put(f"{API}/bookings/{bid}/cancel", json={"cancellation_reason": "TEST cancel"})
        assert c.status_code == 200, f"{c.status_code}: {c.text[:300]}"

        g2 = requests.get(f"{API}/bookings/{bid}")
        assert g2.status_code == 200 and g2.json()["status"] == "cancelled"

        d = admin_client.delete(f"{API}/admin/bookings/{bid}")
        assert d.status_code in (200, 204)

    def test_settings_fields(self):
        r = requests.get(f"{API}/settings")
        assert r.status_code == 200, r.text[:300]
        d = r.json()
        for key in ["phone", "email", "address", "working_hours"]:
            assert key in d, f"missing {key}"
        assert "_id" not in d
