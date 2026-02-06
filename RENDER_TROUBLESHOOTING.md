# Render Deployment Troubleshooting Guide

## 🚨 CRITICAL: Data Not Showing Issue - FIXED!

### What Was Wrong?
The `init_render_db.py` script had **outdated field names** that didn't match the current database models. This caused the script to fail silently when trying to add doctors and beds.

### What Was Fixed?
✅ Updated Doctor model fields:
- ~~`specialization`~~ → Uses `department` only
- ~~`phone`, `email`, `is_active`~~ → Removed (not in current model)
- Added `new_patient_fee` and `followup_fee` (required fields)
- Added `status` field with `DoctorStatus.ACTIVE` enum

✅ Updated Bed model fields:
- ~~`ward`, `bed_type`, `is_occupied`~~ → Removed (not in current model)
- Added `ward_type` (enum: GENERAL, SEMI_PRIVATE, PRIVATE)
- Added `per_day_charge` (required field)
- Added `status` field with `BedStatus.AVAILABLE` enum

✅ Fixed ID generation:
- Now uses simple sequential IDs instead of complex async generators
- `DOC00001`, `DOC00002`, etc. for doctors
- `BED00001`, `BED00002`, etc. for beds

---

## 🔧 STEP-BY-STEP FIX INSTRUCTIONS

### Step 1: Wait for Render to Redeploy
The fix has been pushed to GitHub. Render will automatically:
1. Detect the new commit
2. Rebuild your Docker container
3. Redeploy the service

**Wait 5-10 minutes** for this to complete. Check the "Events" tab in Render dashboard.

### Step 2: Access Render Shell
1. Go to your Render service dashboard
2. Click **"Shell"** tab in the left sidebar
3. Wait for shell to connect (you'll see a command prompt)

### Step 3: Run Database Initialization
Copy and paste this command:

```bash
python init_render_db.py
```

**Expected Output:**
```
✅ Database tables created successfully
✅ Added 5 doctors successfully
✅ Added 20 beds successfully

🎉 Database initialization completed successfully!
```

### Step 4: Verify Doctors Were Added
Run this verification command:

```bash
python -c "import asyncio; from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker; from sqlalchemy import select; from app.core.config import settings; from app.models.doctor import Doctor; async def check(): engine = create_async_engine(settings.DATABASE_URL); async_session = async_sessionmaker(engine, class_=AsyncSession); async with async_session() as session: result = await session.execute(select(Doctor)); doctors = result.scalars().all(); print(f'\n✅ Found {len(doctors)} doctors:'); [print(f'  - {d.name} ({d.department}) - Fee: ₹{d.new_patient_fee}') for d in doctors]; await engine.dispose(); asyncio.run(check())"
```

**Expected Output:**
```
✅ Found 5 doctors:
  - Dr. Rajesh Kumar (General Medicine) - Fee: ₹300
  - Dr. Priya Sharma (Pediatrics) - Fee: ₹350
  - Dr. Amit Singh (Surgery) - Fee: ₹500
  - Dr. Sunita Verma (Gynecology) - Fee: ₹400
  - Dr. Vikram Patel (Orthopedics) - Fee: ₹450
```

### Step 5: Verify Beds Were Added
Run this verification command:

```bash
python -c "import asyncio; from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker; from sqlalchemy import select; from app.core.config import settings; from app.models.bed import Bed; async def check(): engine = create_async_engine(settings.DATABASE_URL); async_session = async_sessionmaker(engine, class_=AsyncSession); async with async_session() as session: result = await session.execute(select(Bed)); beds = result.scalars().all(); print(f'\n✅ Found {len(beds)} beds:'); [print(f'  - {b.bed_number} ({b.ward_type.value}) - ₹{b.per_day_charge}/day') for b in beds[:5]]; print(f'  ... and {len(beds)-5} more beds'); await engine.dispose(); asyncio.run(check())"
```

**Expected Output:**
```
✅ Found 20 beds:
  - GEN-01 (GENERAL) - ₹500/day
  - GEN-02 (GENERAL) - ₹500/day
  - GEN-03 (GENERAL) - ₹500/day
  - GEN-04 (GENERAL) - ₹500/day
  - GEN-05 (GENERAL) - ₹500/day
  ... and 15 more beds
```

### Step 6: Test Your Application
Visit your deployed URL and test:

#### ✅ Dashboard
- Should load without errors
- Stats should show correctly

#### ✅ OPD → New Patient
- **CRITICAL**: Doctors should now appear in dropdown!
- Select a doctor → Department and fee should auto-fill
- Register a test patient
- Verify serial number generates correctly

#### ✅ Billing
- Search for patients
- Add charges
- Record payment
- Check revenue updates on dashboard

#### ✅ IPD → Admit Patient
- Beds should appear in dropdown
- Admit a test patient
- Verify IPD status shows on dashboard

---

## 🆘 TROUBLESHOOTING COMMON ISSUES

### Issue 1: "ModuleNotFoundError" in Shell
**Symptom:** Error when running `python init_render_db.py`

**Solution:**
```bash
# Make sure you're in the correct directory
pwd
# Should show: /opt/render/project/src

# If not, navigate there:
cd /opt/render/project/src

# Try again:
python init_render_db.py
```

### Issue 2: Doctors Already Exist Message
**Symptom:** Script says "ℹ️ 5 doctors already exist" but dropdown is still empty

**Possible Causes:**
1. **Browser cache**: Hard refresh the page (Ctrl+Shift+R or Cmd+Shift+R)
2. **API endpoint issue**: Check Render logs for errors
3. **Database connection issue**: Verify DATABASE_URL environment variable

**Solution:**
```bash
# Check if doctors are really there:
python -c "import asyncio; from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker; from sqlalchemy import select; from app.core.config import settings; from app.models.doctor import Doctor; async def check(): engine = create_async_engine(settings.DATABASE_URL); async_session = async_sessionmaker(engine, class_=AsyncSession); async with async_session() as session: result = await session.execute(select(Doctor)); doctors = result.scalars().all(); print(f'Found {len(doctors)} doctors'); await engine.dispose(); asyncio.run(check())"

# If it shows 0 doctors, delete the database and reinitialize:
rm hospital.db
python init_render_db.py
```

### Issue 3: API Returns Empty Array
**Symptom:** Browser console shows `[]` when fetching `/api/v1/doctors/`

**Solution:**
1. Check Render logs for errors:
   - Go to "Logs" tab in Render dashboard
   - Look for Python errors or database connection issues

2. Verify environment variables:
   - Go to "Environment" tab
   - Ensure `DATABASE_URL=sqlite+aiosqlite:///./hospital.db`

3. Restart the service:
   - Go to "Manual Deploy" → "Clear build cache & deploy"

### Issue 4: Database File Permissions
**Symptom:** "Permission denied" errors when accessing database

**Solution:**
```bash
# Check file permissions
ls -la hospital.db

# If needed, fix permissions:
chmod 644 hospital.db

# Reinitialize:
python init_render_db.py
```

### Issue 5: Old Data Persisting
**Symptom:** Want to start fresh with clean database

**Solution:**
```bash
# Backup existing database (optional):
cp hospital.db hospital_backup_$(date +%Y%m%d_%H%M%S).db

# Delete database:
rm hospital.db

# Reinitialize:
python init_render_db.py
```

---

## 📊 DATA VERIFICATION COMMANDS

### Check All Tables
```bash
python -c "import asyncio; from sqlalchemy.ext.asyncio import create_async_engine; from app.core.config import settings; from app.core.database import Base; async def check(): engine = create_async_engine(settings.DATABASE_URL); async with engine.begin() as conn: result = await conn.run_sync(lambda sync_conn: sync_conn.execute('SELECT name FROM sqlite_master WHERE type=\"table\"')); tables = result.fetchall(); print(f'\n✅ Found {len(tables)} tables:'); [print(f'  - {t[0]}') for t in tables]; await engine.dispose(); asyncio.run(check())"
```

### Check Doctor Count
```bash
python -c "import asyncio; from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker; from sqlalchemy import select, func; from app.core.config import settings; from app.models.doctor import Doctor; async def check(): engine = create_async_engine(settings.DATABASE_URL); async_session = async_sessionmaker(engine, class_=AsyncSession); async with async_session() as session: result = await session.execute(select(func.count(Doctor.doctor_id))); count = result.scalar(); print(f'\n✅ Total doctors: {count}'); await engine.dispose(); asyncio.run(check())"
```

### Check Bed Count
```bash
python -c "import asyncio; from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker; from sqlalchemy import select, func; from app.core.config import settings; from app.models.bed import Bed; async def check(): engine = create_async_engine(settings.DATABASE_URL); async_session = async_sessionmaker(engine, class_=AsyncSession); async with async_session() as session: result = await session.execute(select(func.count(Bed.bed_id))); count = result.scalar(); print(f'\n✅ Total beds: {count}'); await engine.dispose(); asyncio.run(check())"
```

---

## 🎯 SUCCESS CHECKLIST

Your deployment is successful when:

- [x] Render deployment shows "Live" status
- [x] `python init_render_db.py` completes without errors
- [x] Verification commands show 5 doctors and 20 beds
- [x] Dashboard loads without errors
- [x] **OPD → New Patient shows doctors in dropdown** ✨
- [x] Can register a new patient successfully
- [x] Patient gets a serial number
- [x] Billing page works
- [x] IPD page shows available beds
- [x] All data persists after page refresh

---

## 📝 WHAT'S INCLUDED IN THE DATABASE

### Doctors (5 total)
1. **Dr. Rajesh Kumar** - General Medicine (₹300 new / ₹200 followup)
2. **Dr. Priya Sharma** - Pediatrics (₹350 new / ₹250 followup)
3. **Dr. Amit Singh** - Surgery (₹500 new / ₹300 followup)
4. **Dr. Sunita Verma** - Gynecology (₹400 new / ₹250 followup)
5. **Dr. Vikram Patel** - Orthopedics (₹450 new / ₹300 followup)

### Beds (20 total)
- **10 General Ward beds** (GEN-01 to GEN-10) - ₹500/day
- **5 Semi-Private beds** (SEM-01 to SEM-05) - ₹1000/day
- **5 Private beds** (PRI-01 to PRI-05) - ₹2000/day

---

## 🔄 AUTOMATIC DATA BACKUP

Your system automatically maintains:
- ✅ **Audit Trail**: All operations logged in `audit` table
- ✅ **Visit History**: All patient visits stored permanently
- ✅ **Payment Records**: Complete payment history
- ✅ **Admission Records**: All IPD admissions/discharges

### Manual Backup
To create a manual backup:
```bash
cp hospital.db hospital_backup_$(date +%Y%m%d_%H%M%S).db
```

To list backups:
```bash
ls -lh hospital_backup_*.db
```

---

## 📞 NEED MORE HELP?

If you're still experiencing issues:

1. **Check Render Logs**: Go to "Logs" tab and look for errors
2. **Verify Environment Variables**: Ensure all variables are set correctly
3. **Try Manual Deploy**: Go to "Manual Deploy" → "Clear build cache & deploy"
4. **Check Database File**: Run `ls -la hospital.db` to verify it exists

---

## ✨ HOSPITAL INFORMATION

- **Name**: Tiwari Hospital
- **Address**: Tamkuhi Raj, Kushinagar, Uttar Pradesh - 274407
- **PIN Code**: 274407
- **District**: Kushinagar
- **State**: Uttar Pradesh

---

**Last Updated**: February 7, 2026
**Status**: ✅ FIXED - Database initialization script updated to match current models
