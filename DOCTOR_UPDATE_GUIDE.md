# Doctor Update Guide

## Current Doctor List

The system is configured to use these doctors:

1. **Dr. Nitish Tiwari** - Orthopedics (₹500 new / ₹300 followup)
2. **Dr. Muskan Tiwari** - Dentist (₹400 new / ₹250 followup)
3. Dr. Rajesh Kumar - General Medicine (₹300 new / ₹200 followup)
4. Dr. Priya Sharma - Pediatrics (₹350 new / ₹250 followup)
5. Dr. Amit Singh - Surgery (₹500 new / ₹300 followup)

## Problem: Existing Database Has Old Doctors

If your Render database already has data, the new doctors won't be automatically added because seeding only runs on empty databases.

## Solution: Update Doctors Manually

### Option 1: Run Update Script on Render (Recommended)

1. **Push the update script to GitHub:**
   ```bash
   git add update_doctors.py
   git commit -m "Add doctor update script"
   git push origin main
   ```

2. **Wait for Render to deploy** (2-3 minutes)

3. **Run the script on Render:**
   - Go to Render Dashboard
   - Select your service
   - Click "Shell" tab
   - Run:
     ```bash
     python update_doctors.py
     ```

4. **Verify:**
   - Script will show all doctors being updated
   - Check OPD registration page - should show new doctors

### Option 2: Use API to Add Doctors

If you have admin access, you can add doctors via API:

```bash
# Add Dr. Nitish Tiwari
curl -X POST "https://your-app.onrender.com/api/v1/doctors/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Dr. Nitish Tiwari",
    "department": "Orthopedics",
    "new_patient_fee": 500,
    "followup_fee": 300,
    "status": "ACTIVE"
  }'

# Add Dr. Muskan Tiwari
curl -X POST "https://your-app.onrender.com/api/v1/doctors/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Dr. Muskan Tiwari",
    "department": "Dentist",
    "new_patient_fee": 400,
    "followup_fee": 250,
    "status": "ACTIVE"
  }'
```

### Option 3: Clear Database and Re-seed (Nuclear Option)

**⚠️ WARNING: This will delete ALL data!**

Only use if you don't have important data:

1. Go to Render Shell
2. Run:
   ```bash
   rm /data/hospital.db
   ```
3. Restart the service
4. Database will be re-created with new doctors

## What Gets Updated

### Files Already Updated:
✅ `app/main.py` - Auto-seeding function
✅ `init_render_db.py` - Manual init script  
✅ `app/core/config.py` - Hospital name to "Surya Hospital"
✅ `render.yaml` - Environment variables
✅ `app/api/v1/endpoints/slips.py` - Print slip with logo

### Where Doctors Appear:
- OPD Registration dropdown
- Follow-up Registration dropdown
- IPD Admission forms
- Reports and analytics
- Print slips
- Patient visit history

## Verification Steps

After updating doctors:

1. **Go to OPD → New Registration**
2. **Click "Doctor" dropdown**
3. **Verify you see:**
   - Dr. Nitish Tiwari - Orthopedics
   - Dr. Muskan Tiwari - Dentist
   - (and other doctors)

4. **Register a test patient**
5. **Print slip**
6. **Verify slip shows:**
   - Correct doctor name
   - Correct department
   - "SURYA HOSPITAL" header

## Troubleshooting

### Old Doctors Still Showing?

**Cause:** Database wasn't updated

**Fix:** Run `update_doctors.py` script on Render

### New Doctors Not in Dropdown?

**Cause:** Browser cache

**Fix:** Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)

### Script Fails to Run?

**Cause:** Missing dependencies or wrong path

**Fix:** 
```bash
# Make sure you're in the right directory
cd /app
python update_doctors.py
```

## Next Steps

1. **Push update script** to GitHub
2. **Wait for deployment**
3. **Run script on Render** via Shell
4. **Test OPD registration** with new doctors
5. **Print a test slip** to verify everything

## Need Help?

If you encounter issues:
- Share error messages from Render logs
- Let me know which step failed
- I can help troubleshoot or provide alternative solutions
