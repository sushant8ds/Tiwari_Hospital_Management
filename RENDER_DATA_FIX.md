# How to Fix Deployed App Differences and Schema Issues on Render

If your deployed application on Render does not look or function the same as your local development server, it is likely due to **database schema mismatches** and **stale seeded data**.

---

## 🔍 The Root Cause

1. **Database Schema Mismatch**:
   During local development, new columns were added to the `ipd` table (such as `attending_doctor_id`, `referred_by`, `diagnosis`, `procedure_performed`, `operation_date`, and `discount`). 
   FastAPI uses `Base.metadata.create_all` on startup. This function **only creates tables if they do not exist**; it **does not modify existing tables**. Since your Render PostgreSQL database already had the old `ipd` table, the new columns were never added, causing database queries to fail silently or crash on the server.

2. **Incorrect Seeding**:
   An older script (`init_render_db.py`) was run initially, which only seeded 20 beds and used outdated doctor fees. The updated code in `app/main.py` seeds 30 beds and correct fees, but **only if the database is completely empty**. Because the database already had data, the correct seeding never occurred.

---

## 🛠️ Step-by-Step Solution (Resetting Render Database)

To fix this, you must empty/reset the Render database so that the application can automatically recreate the tables with the correct schema and seed the correct initial data on startup.

### Option A: Reset Database via Render Dashboard (Easiest)

1. Go to your **Render Dashboard**.
2. Select your **PostgreSQL Database** (`hospital-postgres-db`).
3. Scroll down to the bottom of the page.
4. Click **"Delete Database"** (or use the drop table commands if you have a database explorer connected).
5. Create a new PostgreSQL database on Render.
6. Copy the new database's **Internal Database URL**.
7. Go to your Web Service (`tiwari-hospital-management`) -> **Environment** tab.
8. Update the `DATABASE_URL` environment variable with the new connection string.
9. Deploy the latest commit. The app will automatically create the correct tables and seed the correct data on startup!

---

### Option B: Drop Existing Tables via Render Shell (Advanced)

If you don't want to delete the database service, you can drop the existing tables directly:

1. Go to your **Render Web Service** dashboard.
2. Click on the **"Shell"** tab in the left sidebar.
3. Wait for it to connect, then run the python command to drop all tables:
   ```bash
   python -c "import asyncio; from app.core.database import engine, Base; async def reset(): async with engine.begin() as conn: await conn.run_sync(Base.metadata.drop_all); print('Dropped all tables!'); asyncio.run(reset())"
   ```
4. If that command completes successfully, restart or redeploy the service.
5. On the next startup, the application's lifespan script will automatically recreate all tables with the correct schema and seed the correct 30 beds, 5 doctors, and default credentials.

---

## 📈 Verification Checklist

After the database is reset and the service redeploys, check your app:
- [ ] You should be able to log in with `admin` / `admin123` or `staff` / `staff123`.
- [ ] Going to **IPD Dashboard** should load active occupancy stats.
- [ ] Admitting a patient should show **30 beds** (including Single AC, Double Non-AC, etc.) instead of the old 20 beds.
- [ ] Creating an OPD visit should show the correct doctor fees (e.g. Dr. Nitish Tiwari = ₹300 consultation fee).
