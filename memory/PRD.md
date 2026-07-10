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
- Promo blocks system
- Gallery integration

### Notifications (Complete)
- Telegram bot subscription flow
- Automated notifications for booking status changes
- Deep linking for client subscription

### Analytics Dashboard (Complete)
- Overall statistics
- Monthly revenue breakdown
- Per-master performance metrics
- Filter by master

### File Storage (Complete)
- Hetzner S3 integration
- Direct browser-to-bucket uploads for gallery
- Presigned URLs for secure access

## Recent Bug Fixes (2025-01-11)

### P0 Bug Fixed: "помилка збереження блоку" (Error saving block)
- **Root Cause:** Missing `/api` prefix in all API calls within `AdminPromoBlocks.js`
- **Fix Applied:** Changed 6 instances of `${API}/admin/...` to `${API}/api/admin/...`
- **Affected File:** `/app/frontend/src/components/admin/AdminPromoBlocks.js`
- **Testing Status:** ✅ PASSED (all CRUD operations verified)

### P1 Fix: Gallery Link Missing in Admin Menu
- **Fix Applied:** Added Gallery menu item and route to AdminDashboard.js
- **Affected File:** `/app/frontend/src/pages/AdminDashboard.js`
- **Testing Status:** ✅ PASSED

## Recent Bug Fixes (2025-01-19)

### P0 Bug Fixed: Reminder Notifications Not Sending
- **Root Cause:** 
  1. No scheduled task was running to check for reminders
  2. Default reminder time was 24 hours instead of 2 hours
- **Fix Applied:**
  - Added APScheduler for automatic reminder checks every 5 minutes
  - Changed default `reminder_hours` from 24 to 2
  - Added startup event to initialize scheduler
  - Added admin endpoints for manual trigger and status check
- **Affected Files:**
  - `/app/backend/server.py` - Added scheduler and endpoints
  - `/app/backend/send_reminders.py` - Updated logic
- **New Endpoints:**
  - `POST /api/admin/send-reminders` - Manual trigger
  - `GET /api/admin/reminder-status` - Check status
- **IMPORTANT:** Clients must subscribe to Telegram bot after booking to receive reminders

## Recent Feature (2025-12-10): Individual Master Telegram Notifications

### Implementation
- **Backend endpoints:**
  - `PATCH /api/masters/{master_id}/telegram` — Save bot token, chat ID, enable/disable
  - `POST /api/masters/{master_id}/test-telegram` — Test message delivery
  - `POST /api/masters/{master_id}/reset-notifications` — Reset unread counter
- **Frontend:** New `MasterTelegramSettings.js` component added to MasterDashboard at `/master/telegram`
- **Notification flow:** On new booking, `notify_master_new_booking()` increments counter and sends Telegram message via master's own bot
- **Testing Status:** PASSED (19/19 backend, 100% frontend)

## Reminder Fix (2025-12-10)

### Issues Fixed
- Timezone: Replaced hardcoded UTC+2 with `Europe/Kyiv` (pytz) for automatic DST handling
- Client telegram_id: Now stored permanently on client record after first subscription. All future bookings get reminders automatically without re-subscribing
- Migrated existing subscriptions to client records (2 clients updated)

### How Reminders Work Now
1. Client books → gets Telegram bot link
2. Client clicks /start once → telegram_id saved to client record permanently
3. Future bookings by same phone → auto-reminders 2h before

## SEO Integration (2025-12-10)

### Implemented
- Meta tags: title, description, keywords, canonical URL (`https://nail-studio.pp.ua/`)
- Open Graph & Twitter Card tags with Soul Nail Studio logo
- JSON-LD Structured Data: `NailSalon` schema with address, phone, email, social links, services
- `sitemap.xml` with public pages (/, /booking, /portfolio, /my-bookings)
- `robots.txt` blocking /admin and /master panels
- Semantic HTML: `<header>`, `<main>`, `<footer>`, role attributes, descriptive alt tags
- Geo tags for local SEO (Дніпропетровська область, Томаківка)
- Brand updated to "Soul Nail Studio" in navigation

### Business Details in SEO
- Phone: +380967920596
- Email: alena19panchenko92@gmail.com
- Address: вул. Шевченка, 3, 2-й поверх, каб. 2, Томаківка
- Facebook: https://www.facebook.com/al.ona.azarcik
- Instagram: https://www.instagram.com/_soul_nail_studio_

## Bug Fix (2025-12-10): Promo Block Images Not Loading After Reload

### Root Cause
Promo blocks stored presigned S3 URLs directly (expire after 1 hour). Gallery images used `file_key` and regenerated URLs on each request — promo blocks did not.

### Fix
- Added `image_key` field to PromoBlock models
- Backend regenerates fresh presigned URLs from `image_key` on every API call
- Frontend sends `file_key` from gallery upload response when creating/updating blocks
- Migrated existing blocks with S3 images to store `image_key`

## Backlog / Future Tasks

### P1 - Refactoring
- [ ] Split `backend/server.py` into feature-specific route files:
  - `routes/masters.py`
  - `routes/bookings.py`
  - `routes/settings.py`
  - `routes/promo_blocks.py`
  - `routes/gallery.py`
  - `routes/telegram.py`
  - `routes/analytics.py`

### P2 - Frontend Architecture
- [ ] Implement centralized React Context for authentication
- [ ] Consolidate duplicated auth logic across components

### P2 - Production Issue (Unconfirmed)
- [ ] Master login failure on production (potential password hash mismatch)
- [ ] Script provided: `/app/reset_master_password.py`
- [ ] Status: Awaiting user confirmation

## API Endpoints Summary

### Public
- `GET /api/promo-blocks` - Active promo blocks
- `GET /api/gallery` - Gallery images
- `POST /api/bookings` - Create booking

### Admin
- `POST /api/admin/login`
- `GET /api/admin/promo-blocks`
- `POST /api/admin/promo-blocks`
- `PUT /api/admin/promo-blocks/{id}`
- `DELETE /api/admin/promo-blocks/{id}`
- `GET /api/admin/stats/monthly`
- `GET /api/admin/stats/masters`

### Master
- `POST /api/masters/login`
- `GET /api/masters/bookings`
- `DELETE /api/bookings/{id}`

## Test Credentials
- **Admin:** admin / admin123
- **Master:** olena@example.com / master123

## Test Reports
- `/app/test_reports/iteration_2.json` - Latest test results
- `/app/tests/test_promo_blocks.py` - Promo blocks test suite
