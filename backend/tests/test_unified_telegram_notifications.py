"""
Unified Telegram notification tests (iteration 7)

Covers the recurring bug: head master / admin bot messages missing client surname
and the new status block.

1) Unit level: notifications.notify_master_new_booking and
   notifications.notify_cancellation_flow must build ONE unified message and
   dispatch it to 3 targets (serving master bot, head master bot, admin bot).
2) E2E: POST /api/bookings, PUT /api/bookings/{id}/cancel,
   PUT /api/admin/bookings/{id} (status=cancelled) must return 200 and dispatch
   without tracebacks.
3) Regression: admin stats endpoints + no leftover telegram_bot.notify_admin_* calls in routes.
"""

import asyncio
import os
import subprocess
import sys
from datetime import datetime, timedelta

import pytest
import requests
from dotenv import dotenv_values

sys.path.insert(0, "/app/backend")

frontend_env = dotenv_values("/app/frontend/.env")
base_url = os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL")
if not base_url:
    raise RuntimeError("REACT_APP_BACKEND_URL missing")
BASE_URL = base_url.rstrip("/")

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

SERVING_MASTER_ID = "197c3a5e-9fe0-4863-90ee-77aa0babd2c8"
SERVING_SERVICE_ID = "28858083-039f-423c-861f-f3f98e09b894"
HEAD_MASTER_ID = "726a7346-f0d5-4f1d-99cc-4b7e1f5795cc"

BACKEND_LOG = "/var/log/supervisor/backend.err.log"


# ---------------------------------------------------------------- shared loop
@pytest.fixture(scope="session")
def loop():
    lp = asyncio.new_event_loop()
    asyncio.set_event_loop(lp)
    yield lp
    lp.close()


@pytest.fixture(scope="session")
def api_client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def admin_token(api_client):
    r = api_client.post(f"{BASE_URL}/api/admin/login",
                        json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})
    if r.status_code != 200:
        pytest.fail(f"Admin login failed: {r.status_code} {r.text[:300]}")
    token = r.json().get("token") or r.json().get("access_token")
    assert token, f"No token in login response: {r.json()}"
    return token


def log_tail(lines=400):
    try:
        return subprocess.run(["tail", "-n", str(lines), BACKEND_LOG],
                              capture_output=True, text=True).stdout
    except Exception:
        return ""


def free_slot(api_client, date):
    r = api_client.get(f"{BASE_URL}/api/timeslots/{date}",
                       params={"service_id": SERVING_SERVICE_ID, "master_id": SERVING_MASTER_ID})
    assert r.status_code == 200, r.text
    for s in r.json():
        if s.get("available"):
            return s["time"]
    return None


def make_booking(api_client, surname="Тестенко-Прізвище"):
    """Create a booking on the first free future slot; returns response json."""
    for offset in range(20, 60):
        date = (datetime.utcnow() + timedelta(days=offset)).strftime("%Y-%m-%d")
        time = free_slot(api_client, date)
        if not time:
            continue
        payload = {
            "master_id": SERVING_MASTER_ID,
            "service_id": SERVING_SERVICE_ID,
            "client_name": "TEST_Клієнт",
            "client_surname": surname,
            "client_phone": "+380991112233",
            "client_email": "test_qa@example.com",
            "date": date,
            "time": time,
            "notes": "TEST_notes",
        }
        r = api_client.post(f"{BASE_URL}/api/bookings", json=payload)
        if r.status_code == 200:
            return r.json()
        if r.status_code != 400:
            pytest.fail(f"POST /api/bookings -> {r.status_code}: {r.text[:400]}")
    pytest.fail("No free slot found for booking creation")


# =========================================================== UNIT: message build
class TestUnifiedMessageDispatch:
    """notifications.py — unified message must reach 3 targets with full content"""

    def _setup_capture(self, monkeypatch):
        import notifications

        master_msgs = []
        admin_msgs = []
        cancel_calls = []

        async def fake_master_send(master_id, message):
            master_msgs.append((master_id, message))
            return True

        async def fake_admin_send(chat_id, text, *a, **kw):
            admin_msgs.append((chat_id, text))
            return True

        async def fake_client_tg_id(booking_id):
            return "555000111"  # pretend client subscribed

        async def fake_send_cancelled(*a, **kw):
            cancel_calls.append(a)
            return True

        monkeypatch.setattr(notifications, "send_master_telegram_notification", fake_master_send)
        monkeypatch.setattr(notifications.telegram_bot, "send_message", fake_admin_send)
        monkeypatch.setattr(notifications.telegram_bot, "get_client_telegram_id", fake_client_tg_id)
        monkeypatch.setattr(notifications.telegram_bot, "send_booking_cancelled", fake_send_cancelled)
        return notifications, master_msgs, admin_msgs, cancel_calls

    @staticmethod
    def _booking():
        return {
            "id": "unit-test-booking-id",
            "master_id": SERVING_MASTER_ID,
            "service_name": "Манікюр",
            "client_name": "Оксана",
            "client_surname": "Прізвиськова",
            "client_phone": "+380990000001",
            "client_email": "oksana@example.com",
            "date": "2026-08-10",
            "time": "12:00",
            "price": 500,
            "notes": "unit note",
        }

    def test_new_booking_dispatches_three_full_messages(self, loop, monkeypatch):
        notifications, master_msgs, admin_msgs, _ = self._setup_capture(monkeypatch)
        booking = self._booking()

        loop.run_until_complete(
            notifications.notify_master_new_booking(booking, "Манікюр", "Марія Петренко", "ADMIN_CHAT")
        )
        # revert unread counter side effect
        loop.run_until_complete(
            notifications.db.masters.update_one({"id": SERVING_MASTER_ID},
                                                {"$inc": {"unread_bookings_count": -1}})
        )

        all_msgs = [m for _, m in master_msgs] + [t for _, t in admin_msgs]
        assert len(all_msgs) == 3, f"expected 3 messages, got {len(all_msgs)}: {master_msgs} {admin_msgs}"

        target_ids = [mid for mid, _ in master_msgs]
        assert SERVING_MASTER_ID in target_ids, target_ids
        assert HEAD_MASTER_ID in target_ids, f"head master not notified: {target_ids}"
        assert admin_msgs[0][0] == "ADMIN_CHAT"

        for msg in all_msgs:
            assert "Прізвиськова" in msg, f"surname missing: {msg}"
            assert "Оксана" in msg
            assert "+380990000001" in msg
            assert "Марія Петренко" in msg
            assert "📲 Клієнт у Telegram" in msg, f"status block missing: {msg}"
            assert "⚠️ Потребує підтвердження!" in msg
            assert "Манікюр" in msg and "2026-08-10" in msg and "12:00" in msg
        # all three identical (single unified message)
        assert len(set(all_msgs)) == 1, "messages differ between channels"

    def test_cancellation_flow_dispatches_three_full_messages(self, loop, monkeypatch):
        notifications, master_msgs, admin_msgs, cancel_calls = self._setup_capture(monkeypatch)
        booking = self._booking()

        loop.run_until_complete(
            notifications.notify_cancellation_flow(booking, "причина", "Марія Петренко", "ADMIN_CHAT")
        )

        assert len(cancel_calls) == 1, "client cancellation notification not attempted"
        all_msgs = [m for _, m in master_msgs] + [t for _, t in admin_msgs]
        assert len(all_msgs) == 3, f"expected 3 messages, got {len(all_msgs)}"

        target_ids = [mid for mid, _ in master_msgs]
        assert SERVING_MASTER_ID in target_ids and HEAD_MASTER_ID in target_ids, target_ids
        assert admin_msgs[0][0] == "ADMIN_CHAT"

        for msg in all_msgs:
            assert "Прізвиськова" in msg, f"surname missing: {msg}"
            assert "📝 Причина: причина" in msg, f"reason missing: {msg}"
            assert "📲 Клієнт у Telegram" in msg, f"subscription line missing: {msg}"
            assert "✉️ Сповіщення клієнту" in msg, f"delivery line missing: {msg}"
            assert "Запис скасовано" in msg
        assert len(set(all_msgs)) == 1, "messages differ between channels"

    def test_unsubscribed_client_marks_not_delivered(self, loop, monkeypatch):
        import notifications
        msgs = []

        async def fake_master_send(master_id, message):
            msgs.append(message)
            return True

        async def none_id(booking_id):
            return None

        monkeypatch.setattr(notifications, "send_master_telegram_notification", fake_master_send)
        monkeypatch.setattr(notifications.telegram_bot, "get_client_telegram_id", none_id)
        loop.run_until_complete(
            notifications.notify_cancellation_flow(self._booking(), "reason2", "Марія Петренко")
        )
        assert msgs, "no dispatch happened"
        for m in msgs:
            assert "❌ не підписаний" in m
            assert "✉️ Сповіщення клієнту: ❌ не надіслано" in m


# ================================================================== E2E flows
class TestBookingNotificationE2E:
    created = []

    def test_create_booking_dispatches_without_error(self, api_client):
        before = len(log_tail(2000))
        data = make_booking(api_client, surname="Прізвиськова")
        assert data.get("id"), data
        assert data.get("client_surname") == "Прізвиськова"
        assert data.get("status") == "pending"
        TestBookingNotificationE2E.created.append(data["id"])

        # persistence
        g = api_client.get(f"{BASE_URL}/api/bookings/{data['id']}")
        assert g.status_code == 200
        assert g.json()["client_surname"] == "Прізвиськова"

        import time as _t
        _t.sleep(6)
        logs = log_tail(2000)[before:]
        assert "Traceback" not in logs, f"traceback after booking create:\n{logs[-2000:]}"
        assert "notify_admin" not in logs, f"legacy notify_admin call in logs:\n{logs[-2000:]}"
        dispatch_hits = [mid for mid in (SERVING_MASTER_ID, HEAD_MASTER_ID)
                         if f"Telegram not configured for master {mid}" in logs
                         or f"notification sent to master {mid}" in logs]
        assert len(dispatch_hits) == 2, f"expected dispatch to both masters, got {dispatch_hits}\n{logs[-2000:]}"

    def test_client_cancel_dispatches_without_error(self, api_client):
        data = make_booking(api_client, surname="Скасувалова")
        bid = data["id"]
        TestBookingNotificationE2E.created.append(bid)
        before = len(log_tail(2000))

        r = api_client.put(f"{BASE_URL}/api/bookings/{bid}/cancel",
                           json={"cancellation_reason": "TEST_причина клієнта"})
        assert r.status_code == 200, r.text
        g = api_client.get(f"{BASE_URL}/api/bookings/{bid}")
        assert g.json()["status"] == "cancelled"
        assert g.json()["cancellation_reason"] == "TEST_причина клієнта"

        import time as _t
        _t.sleep(6)
        logs = log_tail(2000)[before:]
        assert "Traceback" not in logs, f"traceback after cancel:\n{logs[-2000:]}"
        assert "AttributeError" not in logs
        dispatch_hits = [mid for mid in (SERVING_MASTER_ID, HEAD_MASTER_ID)
                         if f"Telegram not configured for master {mid}" in logs
                         or f"notification sent to master {mid}" in logs]
        assert len(dispatch_hits) == 2, f"expected dispatch to both masters, got {dispatch_hits}\n{logs[-2000:]}"

    def test_admin_cancel_dispatches_without_error(self, api_client, admin_token):
        data = make_booking(api_client, surname="Адмінскасована")
        bid = data["id"]
        TestBookingNotificationE2E.created.append(bid)
        before = len(log_tail(2000))

        r = api_client.put(f"{BASE_URL}/api/admin/bookings/{bid}",
                           json={"status": "cancelled", "notes": "TEST_admin reason"},
                           headers={"Authorization": f"Bearer {admin_token}"})
        assert r.status_code == 200, r.text
        g = api_client.get(f"{BASE_URL}/api/bookings/{bid}")
        assert g.json()["status"] == "cancelled"

        import time as _t
        _t.sleep(6)
        logs = log_tail(2000)[before:]
        assert "Traceback" not in logs, f"traceback after admin cancel:\n{logs[-2000:]}"
        dispatch_hits = [mid for mid in (SERVING_MASTER_ID, HEAD_MASTER_ID)
                         if f"Telegram not configured for master {mid}" in logs
                         or f"notification sent to master {mid}" in logs]
        assert len(dispatch_hits) == 2, f"expected dispatch to both masters, got {dispatch_hits}\n{logs[-2000:]}"


# ================================================================ regressions
class TestRegressions:
    def test_no_legacy_notify_admin_calls_in_routes(self):
        out = subprocess.run(
            ["grep", "-rn", "notify_admin_new_booking\\|notify_admin_booking_cancelled",
             "/app/backend/routes", "/app/backend/notifications.py", "/app/backend/scheduler.py"],
            capture_output=True, text=True).stdout
        assert out.strip() == "", f"legacy admin-bot calls still present:\n{out}"

    def test_admin_stats_flat_fields(self, api_client, admin_token):
        h = {"Authorization": f"Bearer {admin_token}"}
        r = api_client.get(f"{BASE_URL}/api/admin/stats", headers=h)
        assert r.status_code == 200, r.text
        d = r.json()
        for k in ("total_bookings", "today_bookings", "pending_bookings", "confirmed_bookings",
                  "total_revenue"):
            assert k in d, f"{k} missing in {d}"
            assert isinstance(d[k], (int, float))
        assert "_id" not in d

    def test_admin_stats_masters(self, api_client, admin_token):
        h = {"Authorization": f"Bearer {admin_token}"}
        r = api_client.get(f"{BASE_URL}/api/admin/stats/masters", headers=h)
        assert r.status_code == 200, r.text
        rows = r.json()
        assert isinstance(rows, list) and rows
        for row in rows:
            for k in ("master_id", "master_name", "total_bookings", "confirmed", "completed",
                      "cancelled", "revenue"):
                assert k in row, f"{k} missing in {row}"
            assert "_id" not in row and "password_hash" not in row

    def test_admin_stats_monthly(self, api_client, admin_token):
        h = {"Authorization": f"Bearer {admin_token}"}
        r = api_client.get(f"{BASE_URL}/api/admin/stats/monthly", params={"year": 2026}, headers=h)
        assert r.status_code == 200, r.text
        rows = r.json()
        assert len(rows) == 12, rows
        for row in rows:
            assert "month_name" in row and "total_bookings" in row and "revenue" in row
