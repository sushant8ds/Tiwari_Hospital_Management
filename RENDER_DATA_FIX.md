# Fix: Data Not Persisting on Render

## Problem
SQLite database was being stored in ephemeral filesystem, so data was lost on every deployment/restart.

## Solution Applied
Added Render persistent disk to store the database permanently.

## Changes Made

### 1. Updated `render.yaml`
- Added persistent disk configuration:
  ```yaml
  disk:
    name: hospital-data
    mountPath: /data
    sizeGB: 1
  ```
- Changed DATABASE_URL to use persistent disk:
  ```yaml
  DATABASE_URL: sqlite+aiosqlite:////data/hospital.db
  ```

### 2. Updated `Dockerfile`
- Created `/data` directory
- Set proper permissions for the data directory

## Deployment Steps

1. **Commit and push changes:**
   ```bash
   git add render.yaml Dockerfile
   git commit -m "Add persistent disk for database storage"
   git push origin main
   ```

2. **Render will automatically:**
   - Create a 1GB persistent disk
   - Mount it at `/data`
   - Store the database there permanently

3. **After deployment:**
   - The app will auto-seed doctors and beds on first startup
   - Data will persist across deployments and restarts
   - Check logs to confirm: "✅ Added 5 doctors successfully"

## Verify It's Working

1. Visit your Render dashboard
2. Go to your service → "Disks" tab
3. You should see "hospital-data" disk mounted at `/data`

4. Check the logs after deployment:
   ```
   📊 No doctors found. Seeding initial doctors...
   ✅ Added 5 doctors successfully
   🛏️  No beds found. Seeding initial beds...
   ✅ Added 20 beds successfully
   ```

5. Test the app:
   - Go to OPD → New Registration
   - Doctor dropdown should show 5 doctors
   - Go to IPD → Admit Patient
   - Bed dropdown should show 20 beds

## Important Notes

- **First deployment**: Data will be seeded automatically
- **Subsequent deployments**: Data persists, no re-seeding
- **Disk size**: 1GB is plenty for SQLite (can store millions of records)
- **Backups**: Consider downloading database backups periodically

## If Data Still Doesn't Show

1. Check Render logs for errors during startup
2. Verify disk is mounted: Look for "hospital-data" in Render dashboard
3. SSH into Render (if available) and check:
   ```bash
   ls -la /data
   ```

## Cost Note
Persistent disks on Render Starter plan are included, no extra cost for 1GB.
