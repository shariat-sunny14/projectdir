# Factory Fleet Management System — MVP

A Next.js + TypeScript fleet management app with JSON-file persistence, real email
delivery, Google sign-in, and the full booking → approval → trip lifecycle wired up
end to end.

## Getting started

```bash
npm install
npm run seed     # demo departments, vehicles, drivers, one account per role
npm run dev       # http://localhost:3000
```

### Demo accounts (password `Passw0rd!`)

| Role | Email |
|---|---|
| Super Admin | `admin@fleet.local` |
| Admin | `admin.user@fleet.local` |
| Transport Manager | `manager@fleet.local` |
| Employee | `employee@fleet.local` |
| Driver | `driver@fleet.local` |

## ⚠️ Credentials in `.env` — rotate before real use

`.env` ships with a working Gmail SMTP app password and a Google OAuth Client
ID/Secret so email and "Continue with Google" work immediately. **Because these were
shared in plain text in chat, treat them as already compromised**:
- Regenerate a Gmail [app password](https://myaccount.google.com/apppasswords).
- Regenerate the Google OAuth client secret (and consider a new Client ID) at
  https://console.cloud.google.com/apis/credentials.
- Add your real domain(s) to that OAuth client's **Authorized JavaScript origins**
  (e.g. `http://localhost:3000` for local dev, your real domain for production) —
  Google will reject the sign-in popup otherwise.

`.env` is in `.gitignore` so it won't get committed if you push this to a repo.

## Latest round of changes

- **Admin Dashboard filters + charts** — Today / Last 7 Days / Last Month / Last 6
  Months / Last 1 Year presets plus a custom From–To range, all URL-driven. Three
  premium `recharts`-based charts: a gradient-filled Bookings Trend area chart
  (auto-buckets by day/week/month depending on the range span), a Vehicle Status
  donut, and an Expenses-by-Category bar chart.
- **Date-range filter + pagination on every high-volume list** — Vehicles, Drivers,
  All Bookings, Service/Maintenance, Expenses, Employees, Departments, User Approvals
  History, Email Logs, and Audit Logs all now have a `DateRangeFilter` (same presets
  as the dashboard) and page-based `Pagination` (10 rows/page), both reflected in the
  URL so filtered/paginated views are shareable and survive a refresh.
- **Mobile responsiveness sweep** — every modal form's rigid `grid-cols-2`/`grid-cols-3`
  now stacks to a single column on small screens and expands at `sm:`; page headers
  that used to force title+button onto one row now wrap on mobile; pagination controls
  wrap instead of overflowing on narrow viewports.

## Previous round of changes

1. **Notification bell** always refetches when opened (no more stale data) and polls
   every 15s.
2. **Auto Starting/Ending KM** — fixed: `TripPanel` now remounts on booking/trip state
   change, so KM fields populate immediately after Approve / Start Trip, no reload.
3. **Time picker** — booking wizard's start/end time fields now have a clock icon that
   opens the picker on click.
4–5. **Role-based portals** — distinct dashboards, sidebar menus, and mobile bottom nav
   per role (Employee/Driver/Admin/Manager); booking approval only exists on
   admin/manager-reachable routes, gated server-side.
6. *(Not implemented — see below)*
7. **Date picker modal overflow** — fixed by rendering the calendar via a React portal
   with viewport-aware positioning, so it can't be clipped by a modal's scroll area
   anymore.
8. **Employee edit — all fields** — full name, email, employee ID, department,
   designation, address, role, and status are all editable from one modal.
9. **Email Logs** — Sent/Failed badge with the error message on failure, plus a working
   **Resend** button.
10–11. **Maintenance form** — Current KM auto-fills from the selected vehicle; Invoice
   Number auto-generates (still editable).
12. *(Not implemented as OTP — see below)*
13. **"Continue with Google"** works for both sign-in and sign-up, using Google
   Identity Services + server-side ID token verification (`google-auth-library`).
   New Google sign-ups still go through a short "finish your profile" step (phone,
   department, designation) and land as `PENDING`, requiring the same admin approval
   as a normal sign-up.
14. *(Not implemented — see below)*
15. **Manual employee creation** — admins/managers can add an employee (or
   driver/manager/admin, role-gated) directly, with a temporary password.
16. **Driver dashboard** — a prominent "You are currently ON TRIP" banner links
   straight into the active trip.
17. **Dashboard "Approved Vehicles" count** added to the admin dashboard.
18. **Cancel restriction enforced server-side** — once a booking is `APPROVED`, only
   `SUPER_ADMIN`/`ADMIN` can cancel it; the employee can only self-cancel while
   `PENDING`.
19. **Driver-submitted Maintenance/Expense entries with admin approval** — drivers get
   Maintenance/Expenses in their sidebar with a simplified submit form (including a
   document/receipt upload — JPG/PNG/PDF, saved to `/public/uploads`). Entries land as
   `PENDING`; the vehicle's status only changes once an admin approves. Admins see a
   Document link and Approve/Reject controls on every pending entry, plus who
   submitted it.
20. **Notifications on every entry type** — booking created/approved/rejected/
   cancelled, vehicle changed, trip completed, account approved/rejected, password
   reset, and now maintenance/expense submitted/approved/rejected all create an
   in-app notification (and, where relevant, an email).

### Not implemented this round

- **#6 — Uber-style pickup/destination search.** Pickup/Destination are still plain
  text fields. A real implementation needs a geocoding provider (Google Places,
  Mapbox, or a free OpenStreetMap/Nominatim lookup) wired into a debounced
  autocomplete component — happy to build this as a follow-up once you pick a
  provider (Nominatim needs no API key but has stricter rate limits; Google Places
  needs a billing-enabled API key).
- **#12 — OTP-based password reset.** The current flow is link-based (see
  "Password reset" below) rather than a 6-digit OTP. Converting it is a moderate
  change (new short-lived OTP codes instead of long tokens, a 3-step UI) that didn't
  fit in this round.
- **#14 — Live vehicle tracking.** This was explicitly out of scope in the original
  3-day MVP spec (GPS/live location/Maps were called out as "do not spend the
  deadline on this"). A realistic version needs either a GPS/telematics device in
  each vehicle or the driver's phone reporting location while on a trip (browser
  `navigator.geolocation`, periodically posted to the server), plus a map view.
  Worth scoping properly as its own feature rather than bolting on quickly.

## Password reset (current, link-based)

`Forgot password?` on the login page → enter email → a 30-minute reset link is
emailed → set a new password. Tokens are single-use, and the response is
intentionally the same whether or not the email exists (avoids account
enumeration).

## Project structure

```
app/
  (app)/              protected routes — shared layout, redirects to /login if no session
    dashboard/         role-specific dashboards (incl. driver ON_TRIP banner)
    bookings/          list, [id] detail (approve/reject/change vehicle/trip), new (wizard)
    admin/             departments, vehicles, drivers, employees (+create/edit/role),
                        user-approvals (+role), email-logs (+resend), audit-logs
    maintenance/, expenses/   driver submit + admin approval queues, reports/
  login/, signup/       public auth pages (Google sign-in wired into both)
  forgot-password/, reset-password/
  api/                    route handlers (available-vehicles; everything else uses
                           Server Actions)
lib/
  json-db/                core read/write/update engine, generic repository, per-entity repos
  services/                auth, availability, booking, trip, notification, email,
                            audit, password-reset, google-auth, upload
  actions/                  Server Actions called from forms/buttons
  validators/, auth/, permissions/, errors.ts, types.ts
data/                      JSON "database" files
public/uploads/             driver-submitted maintenance/expense documents
components/
  layout/                   Sidebar (role-based), Header, MobileNav, NotificationBell
  ui/                       Button, Field, StatusBadge, DatePicker, TimePicker
  auth/                     GoogleSignInButton
scripts/seed.ts             demo data seed script
```

## Notes on the JSON persistence layer

Two overlapping writes to the same file are serialized through an in-process promise
queue (`lib/json-db/core.ts`), and every write goes to a temp file that's atomically
renamed over the target — a crash mid-write can't leave a half-written JSON file. This
is adequate for a single Node.js process; for multiple instances behind a load
balancer, replace the JSON layer with a real database.

## Environment variables

See `.env.example`. `SESSION_SECRET` should be a long random string in production.
`YAGMAIL_USER`/`YAGMAIL_APP_PASSWORD` are Gmail SMTP credentials for
`lib/services/email-service.ts`. `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET`/
`NEXT_PUBLIC_GOOGLE_CLIENT_ID` are for "Continue with Google" — the Client ID is
duplicated with the `NEXT_PUBLIC_` prefix because the Google Identity Services button
runs in the browser and needs it client-side.
