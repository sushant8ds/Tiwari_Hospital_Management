# Post-Deployment Checklist for Render

## ✅ Completed
- [x] Fixed async SQLite driver issue (added aiosqlite)
- [x] Fixed email validator dependency
- [x] Updated hospital address to: **Tamkuhi Raj, Kushinagar, Uttar Pradesh - 274407**
- [x] Created database initialization script
- [x] **FIXED: Updated init_render_db.py to match current Doctor and Bed models** ✨
- [x] Pushed all changes to GitHub

## 🚀 Next Steps (DO THIS NOW)

### IMPORTANT: Database Script Was Fixed!
The `init_render_db.py` script had outdated field names. This has been **FIXED** and pushed to GitHub.

**Render will automatically redeploy** when it detects the new commit. Wait 5-10 minutes for the rebuild.

### 1. Wait for Render Deployment
- Render will automatically detect the new commit
- Wait 5-10 minutes for build to complete
- Check that deployment status shows "Live"

### 2. Initialize Database via Render Shell

**CRITICAL**: The database is empty after deployment. You MUST run this:

1. Go to your Render service dashboard
2. Click **"Shell"** tab
3. Run this command:
   ```bash
   python init_render_db.py
   ```

This will:
- ✅ Create all database tables
- ✅ Add 5 doctors with correct fees (so they show in OPD dropdown)
- ✅ Add 20 beds across 3 ward types (General, Semi-Private, Private)
- ✅ Set up the system for use

**What's Different Now:**
- Doctors now have `new_patient_fee` and `followup_fee` fields
- Beds now have `ward_type` (GENERAL/SEMI_PRIVATE/PRIVATE) and `per_day_charge`
- All fields match the current database models ✅

### 3. Update Environment Variable (Optional)

If you want to update the phone number:
1. Go to **Environment** tab in Render
2. Find `HOSPITAL_PHONE`
3. Update to your actual phone number
4. Save (will trigger redeploy)

### 4. Test Everything

Visit your deployed URL and verify:

#### Dashboard
- [ ] Dashboard loads without errors
- [ ] Stats show correctly
- [ ] No "Login required" errors

#### OPD (New Patient)
- [ ] Doctors appear in dropdown ✅ (This was the issue!)
- [ ] Can register new patient
- [ ] Serial number generates correctly
- [ ] Can create visit

#### Billing
- [ ] Can search for patients
- [ ] Can add charges
- [ ] Payment records correctly
- [ ] Revenue updates on dashboard

#### IPD
- [ ] Beds show in dropdown
- [ ] Can admit patient
- [ ] IPD status shows on dashboard

## 📊 Data Backup & History

### Automatic History Tracking
The system automatically maintains:
- ✅ **Audit Trail**: All operations logged in `audit` table
- ✅ **Visit History**: All patient visits stored permanently
- ✅ **Payment Records**: Complete payment history
- ✅ **Admission Records**: All IPD admissions/discharges

### Manual Backup (Via Shell)
To create a backup:
```bash
cp hospital.db hospital_backup_$(date +%Y%m%d_%H%M%S).db
```

To list backups:
```bash
ls -lh hospital_backup_*.db
```

## 🆘 If Doctors Still Don't Show

1. **Check Shell Output**: Make sure `init_render_db.py` ran successfully
2. **Verify Database**: Run in Shell:
   ```bash
   python -c "import asyncio; from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker; from sqlalchemy import select; from app.core.config import settings; from app.models.doctor import Doctor; async def check(): engine = create_async_engine(settings.DATABASE_URL); async_session = async_sessionmaker(engine, class_=AsyncSession); async with async_session() as session: result = await session.execute(select(Doctor)); doctors = result.scalars().all(); print(f'Found {len(doctors)} doctors'); for d in doctors: print(f'  - {d.name} ({d.specialization})'); await engine.dispose(); asyncio.run(check())"
   ```

3. **Re-run Init**: If no doctors found, run `python init_render_db.py` again

## 📝 Hospital Details

- **Name**: Tiwari Hospital
- **Address**: Tamkuhi Raj, Kushinagar, Uttar Pradesh - 274407
- **PIN Code**: 274407
- **District**: Kushinagar
- **State**: Uttar Pradesh

## ✨ What's Fixed

1. **Database Driver**: Now uses `aiosqlite` for async SQLite
2. **Email Validation**: Added `email-validator` package
3. **Hospital Address**: Updated to correct location
4. **Database Init**: Automated script to populate doctors and beds
5. **Data Persistence**: All history stored in SQLite database
6. **Audit Trail**: Complete tracking of all operations

## 🎯 Success Criteria

Your deployment is successful when:
- ✅ Dashboard loads without errors
- ✅ Doctors show in OPD dropdown
- ✅ Can register patients
- ✅ Can create visits
- ✅ Billing works
- ✅ Payments record correctly
- ✅ IPD shows beds
- ✅ All data persists across page refreshes
