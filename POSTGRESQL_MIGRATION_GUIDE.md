# PostgreSQL Migration Guide

## Overview
The hospital management system has been migrated from SQLite to PostgreSQL for better performance, reliability, and scalability in production.

## Changes Made

### 1. Database Configuration
- **Updated**: `app/core/config.py`
  - Added `get_database_url()` function to handle Render's PostgreSQL URL format
  - Default DATABASE_URL now points to PostgreSQL
  - Automatically converts `postgres://` to `postgresql+asyncpg://`

### 2. Dependencies
- **Updated**: `requirements.txt`
  - Added `asyncpg==0.29.0` for async PostgreSQL support
  - Kept `aiosqlite` for local testing

### 3. Render Configuration
- **Updated**: `render.yaml`
  - Removed disk mount (no longer needed for SQLite)
  - Added PostgreSQL database configuration
  - Database name: `hospital-postgres-db`
  - Plan: starter (free tier)

## Deployment on Render

When you push these changes to GitHub, Render will automatically:

1. **Create a PostgreSQL database** (if it doesn't exist)
2. **Connect your web service** to the database
3. **Run migrations** automatically on startup
4. **Seed initial data** (doctors and beds)

## Local Development

### Option 1: Use PostgreSQL Locally

1. Install PostgreSQL on your machine
2. Create a database:
   ```bash
   createdb hospital_db
   ```

3. Update your `.env` file:
   ```
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/hospital_db
   ```

4. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

### Option 2: Use SQLite for Local Development

1. Update your `.env` file:
   ```
   DATABASE_URL=sqlite+aiosqlite:///./hospital.db
   ```

2. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

## Benefits of PostgreSQL

1. **Better Performance**: Handles concurrent users better than SQLite
2. **Data Integrity**: ACID compliance with better transaction support
3. **Scalability**: Can handle larger datasets
4. **Production Ready**: Industry standard for web applications
5. **Backup & Recovery**: Better tools for database backups
6. **No File Locking**: Multiple processes can access simultaneously

## Database Schema

The database schema remains the same. All tables will be automatically created on first startup:

- patients
- doctors
- visits
- beds
- ipd
- billing_charges
- employees
- salary_payments
- audit_logs
- users
- slips
- ot_procedures
- payments

## Troubleshooting

### Connection Issues

If you see connection errors:

1. Check that DATABASE_URL is set correctly
2. Verify PostgreSQL is running (on Render, check database status)
3. Check database credentials

### Migration Issues

If tables aren't created:

1. Check application logs for errors
2. Verify database permissions
3. Try running migrations manually:
   ```bash
   alembic upgrade head
   ```

## Cost

- **Render PostgreSQL Starter Plan**: Free
- **Storage**: 1GB included
- **Connections**: Sufficient for small to medium hospitals

## Next Steps

After deployment:

1. Verify the application starts successfully
2. Check that initial doctors and beds are seeded
3. Test OPD registration
4. Test all Owner panel functions
5. Monitor database performance in Render dashboard

## Rollback (if needed)

If you need to rollback to SQLite:

1. Update `render.yaml` to use disk mount again
2. Change DATABASE_URL back to SQLite
3. Redeploy

However, PostgreSQL is recommended for production use.
