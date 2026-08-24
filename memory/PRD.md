# Nail Studio - Multi-Master Booking System PRD

## Original Problem Statement
Система бронювання для салону краси з підтримкою кількох майстрів. Включає:
- Booking system для клієнтів
- Admin panel для управління
- Master dashboard для майстрів
- Homepage CMS з динамічним контентом
- Галерея робіт з S3 інтеграцією
- Telegram bot для сповіщень клієнтів
- Аналітика для адміна

## Tech Stack
- **Backend:** FastAPI, Motor (async MongoDB), Boto3 (Hetzner S3)
- **Frontend:** React, Tailwind CSS, Shadcn/UI, Recharts
- **Database:** MongoDB
- **File Storage:** Hetzner S3 Object Storage
- **Notifications:** Telegram Bot (webhook-based)

## What's Been Implemented

### Core Features (Complete)
- Multi-master booking system
- Admin authentication (admin/admin123)
- Master authentication
- Service management
- Client management
- Booking management with date filtering and deletion

### Homepage CMS (Complete)
- Dynamic content editing
- Promo blocks system with S3 presigned URLs
- Gallery integration

### Notifications (Complete)
- Telegram bot subscription flow (webhook-based)
- Automated client reminders (APScheduler, Europe/Kyiv timezone)
- Individual master Telegram bots for new booking alerts
- Admin bot with master name in notifications
- Deep linking for client subscription
- **Head master system (2026-08-20):** first-created master auto-marked `is_head=true`; head master receives Telegram notifications (new bookings + cancellations) for ALL masters, others only their own. Messages include master name, client full name (name+surname), phone, email. Admin can reassign head via crown button in Masters page (`PUT /api/masters/{id}/set-head`).
- **Client subscription/delivery status (2026-08-21):** master messages include "📲 Клієнт у Telegram: підписаний/ні" and "✉️ Сповіщення клієнту: надіслано/ні". Admin-side cancellation now also notifies the client.
- **Reminder status to masters (2026-08-21):** when the scheduler sends (or fails to send) a pre-visit reminder to a client, serving master + head master get a Telegram message with delivery status. Failure notification sent once per booking (`reminder_master_notified` flag).
- **Settings fix (2026-08-21):** `/api/settings` routes rewritten to preserve all frontend field names (phone, address, working_hours...) — previously the refactored SiteSettings model (studio_* fields) filtered them out, hiding contacts on prod.
- **Unified notification format (2026-08-22):** RECURRING BUG fixed. Head master/owner receives copies via ADMIN bot (ADMIN_TELEGRAM_ID), which previously used old short format without surname/status. Now new-booking, cancellation AND reminder-status messages build ONE unified message (master name, client name+surname, phone, email, service, date/time, price, subscription + delivery status) dispatched to: serving master bot, head master bot, admin bot. Old telegram_bot.notify_admin_new_booking/notify_admin_booking_cancelled deleted. Client-supplied strings HTML-escaped. Tested: iteration_7 (10/10).
- **Bug fixed (2026-08-20):** booking cancellation returned 500 (called non-existent `notify_client_booking_cancelled` / `notify_client_booking_confirmed`; renamed to `send_booking_cancelled` / `send_booking_confirmed`).

### Analytics Dashboard (Complete)
- Overall statistics
- Monthly revenue breakdown
- Per-master performance metrics
- Filter by master
- **Fixed (2026-08-21):** `/admin/stats/masters` and `/admin/stats/monthly` now return flat field names matching AdminOverview.js (master_name, confirmed, completed, cancelled, revenue, month_name in Ukrainian); "today" stat uses Europe/Kyiv timezone. Tested: iteration_6 (11/11 backend, 5/5 frontend).

### File Storage (Complete)
- Hetzner S3 integration
- Direct browser-to-bucket uploads for gallery
- Presigned URLs for secure access
- Thumbnails (Pillow-generated 400px WebP) for new gallery uploads

### SEO (Complete)
- Meta tags, JSON-LD (NailSalon), Open Graph, sitemap.xml, robots.txt
- Semantic HTML, geo tags for local SEO

### Backend Architecture (Complete - Refactored)
- Modular router structure: `/app/backend/routes/`
- Thin `server.py` entry point
- Separated: `database.py`, `auth.py`, `models.py`, `helpers.py`, `notifications.py`, `scheduler.py`, `s3_utils.py`, `telegram_bot.py`, `telegram_webhook.py`

### Frontend Auth Context (Complete - 2026-08-06)
- Centralized `AuthContext.js` with `loginAdmin()`, `loginMaster()`, `logout()`
- `api.js` axios instance with auto-token interceptor
- `ProtectedRoute` component for role-based route protection
- Removed all direct `localStorage.getItem` calls from 13 files
- All admin components use `useAuth()` hook and `api` instance
- Cross-role protection (master can't access admin routes and vice versa)
- **Testing:** 12/12 frontend scenarios passed

## API Endpoints Summary

### Public
- `GET /api/promo-blocks` - Active promo blocks
- `GET /api/gallery` - Gallery images (with skip/limit pagination)
- `POST /api/bookings` - Create booking
- `GET /api/settings` - Site settings

### Admin
- `POST /api/admin/login`
- `GET /api/admin/promo-blocks`, `POST`, `PUT/{id}`, `DELETE/{id}`
- `GET /api/admin/stats`, `/stats/monthly`, `/stats/masters`
- `PUT /api/admin/settings`

### Master
- `POST /api/masters/login`
- `PATCH /api/masters/{id}/telegram`
- `POST /api/masters/{id}/test-telegram`
- `POST /api/masters/{id}/reset-notifications`
- `PUT /api/masters/{id}/set-head` (admin only, reassign head master)
- `GET/PUT /api/masters/{id}/notes/{date}`

## Test Credentials
- **Admin:** admin / admin123
- **Master:** olena@example.com / test123 (Master ID: 726a7346-f0d5-4f1d-99cc-4b7e1f5795cc)

## Backlog / Future Tasks

### P2 - Gallery Optimization
- [ ] Generate thumbnails for existing older gallery photos in S3

### P2 - Production Issue (Unconfirmed)
- [ ] Master login failure on production (potential password hash mismatch)
- [ ] Script provided: `/app/reset_master_password.py`

### P3 - Cleanup
- [ ] Remove `server_old.py` and test scripts (`test_6_month_booking.py`, `backend_test.py`, etc.)

## Code Architecture
```
/app/
├── backend/
│   ├── server.py             # Thin entry point (FastAPI app, startup/shutdown)
│   ├── database.py           # MongoDB connection logic
│   ├── models.py             # All Pydantic models
│   ├── auth.py               # JWT and password hashing
│   ├── helpers.py            # Phone validation, etc.
│   ├── notifications.py      # Master HTTPX notification logic
│   ├── scheduler.py          # APScheduler logic (Europe/Kyiv timezone)
│   ├── s3_utils.py           # Boto3 logic + Pillow thumbnail generation
│   ├── telegram_bot.py       # Admin HTTPX bot logic
│   ├── telegram_webhook.py   # Webhook for client bot
│   └── routes/               # Modular API routes
├── frontend/
│   └── src/
│       ├── context/
│       │   ├── AuthContext.js     # Centralized auth state (NEW)
│       │   ├── SettingsContext.js
│       │   └── ThemeContext.js
│       ├── lib/
│       │   ├── api.js             # Axios instance with auto-token (NEW)
│       │   └── utils.js
│       ├── components/admin/      # All use useAuth() and api instance
│       └── pages/                 # Login pages use AuthContext
```

## Test Reports
- `/app/test_reports/iteration_3.json` - Telegram notification settings tests
- `/app/test_reports/iteration_4.json` - Auth Context refactor tests (12/12 passed)
