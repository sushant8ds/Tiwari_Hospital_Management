"""
Hospital OPD-IPD Management System
Main FastAPI application entry point
"""

from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
import time
import uuid

from app.core.config import settings
from app.core.database import engine, get_db
from app.core.templates import templates
from app.core.logging import setup_logging, logger
from app.models import Base
from app.api.v1.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    setup_logging()
    logger.info("Starting Hospital Management System...")
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Auto-seed database with initial data if empty
    await seed_initial_data()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Hospital Management System...")


async def seed_initial_data():
    """Automatically seed database with initial doctors, beds, and users if empty"""
    from decimal import Decimal
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    from sqlalchemy import select
    from app.models.doctor import Doctor, DoctorStatus
    from app.models.bed import Bed, WardType, BedStatus
    from app.models.user import User, UserRole
    from app.core.security import get_password_hash
    
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        # Check if users exist, seed if not
        async with async_session() as session:
            result = await session.execute(select(User))
            existing_users = result.scalars().all()
            if not existing_users:
                print("👤 No users found. Seeding admin and staff accounts...")
                
                admin_user = User(
                    user_id="U00001",
                    username="admin",
                    email="admin@hospital.com",
                    hashed_password=get_password_hash("admin123"),
                    full_name="System Administrator",
                    role=UserRole.ADMIN,
                    is_active=True
                )
                session.add(admin_user)
                
                staff_user = User(
                    user_id="U00002",
                    username="staff",
                    email="staff@hospital.com",
                    hashed_password=get_password_hash("staff123"),
                    full_name="Reception Staff",
                    role=UserRole.RECEPTION,
                    is_active=True
                )
                session.add(staff_user)
                
                await session.commit()
                print("✅ Seeded default users: admin/admin123 and staff/staff123")
            else:
                print(f"ℹ️  Database already has {len(existing_users)} users")

        # Check if doctors exist
        async with async_session() as session:
            result = await session.execute(select(Doctor))
            existing_doctors = result.scalars().all()
            
            if not existing_doctors:
                print("📊 No doctors found. Seeding initial doctors...")
                doctors_data = [
                    {"name": "Dr. Nitish Tiwari", "department": "Orthopedics", "new_fee": 300, "followup_fee": 150},
                    {"name": "Dr. Muskan Tiwari", "department": "Dentist", "new_fee": 300, "followup_fee": 150},
                    {"name": "Dr. Rajesh Kumar", "department": "General Medicine", "new_fee": 300, "followup_fee": 150},
                    {"name": "Dr. Priya Sharma", "department": "Pediatrics", "new_fee": 300, "followup_fee": 150},
                    {"name": "Dr. Amit Singh", "department": "Surgery", "new_fee": 300, "followup_fee": 150},
                ]
                
                for idx, doc_data in enumerate(doctors_data, start=1):
                    doctor = Doctor(
                        doctor_id=f"DOC{idx:05d}",
                        name=doc_data["name"],
                        department=doc_data["department"],
                        new_patient_fee=Decimal(str(doc_data["new_fee"])),
                        followup_fee=Decimal(str(doc_data["followup_fee"])),
                        status=DoctorStatus.ACTIVE
                    )
                    session.add(doctor)
                
                await session.commit()
                print(f"✅ Added {len(doctors_data)} doctors successfully")
            else:
                print(f"ℹ️  Database already has {len(existing_doctors)} doctors")
        
        # Check if beds exist
        async with async_session() as session:
            result = await session.execute(select(Bed))
            existing_beds = result.scalars().all()
            
            if not existing_beds:
                print("🛏️  No beds found. Seeding initial beds...")
                beds_data = [
                    # General Ward (10 beds, charge 500)
                    {"prefix": "GEN", "ward": WardType.GENERAL, "count": 10, "charge": 500},
                    # Double sharing non-AC (5 beds, charge 700)
                    {"prefix": "DNAC", "ward": WardType.SEMI_PRIVATE, "count": 5, "charge": 700},
                    # Double sharing AC (5 beds, charge 1100)
                    {"prefix": "DAC", "ward": WardType.SEMI_PRIVATE, "count": 5, "charge": 1100},
                    # Single Private non-AC (5 beds, charge 1000)
                    {"prefix": "SNAC", "ward": WardType.PRIVATE, "count": 5, "charge": 1000},
                    # Single Private AC (5 beds, charge 1500)
                    {"prefix": "SAC", "ward": WardType.PRIVATE, "count": 5, "charge": 1500},
                ]
                
                bed_counter = 1
                for ward_info in beds_data:
                    for i in range(1, ward_info["count"] + 1):
                        bed = Bed(
                            bed_id=f"BED{bed_counter:05d}",
                            bed_number=f"{ward_info['prefix']}-{i:02d}",
                            ward_type=ward_info["ward"],
                            per_day_charge=Decimal(str(ward_info["charge"])),
                            status=BedStatus.AVAILABLE
                        )
                        session.add(bed)
                        bed_counter += 1
                
                await session.commit()
                total_beds = sum(w["count"] for w in beds_data)
                print(f"✅ Added {total_beds} beds successfully")
            else:
                print(f"ℹ️  Database already has {len(existing_beds)} beds")
        
        print("✅ Database initialization complete!")
        
    except Exception as e:
        print(f"⚠️  Error seeding initial data: {str(e)}")
        print("   You may need to run: python init_render_db.py manually")


# Create FastAPI application
app = FastAPI(
    title="Hospital OPD-IPD Management System",
    description="Comprehensive hospital management system for OPD, IPD, billing, and operations",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_and_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = (time.perf_counter() - start_time) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
    return response


# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root(request: Request):
    """Root endpoint - redirect to dashboard"""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "hospital_name": settings.HOSPITAL_NAME,
            "hospital_address": settings.HOSPITAL_ADDRESS,
            "hospital_phone": settings.HOSPITAL_PHONE
        }
    )


@app.get("/login")
async def login_page(request: Request):
    """User login page"""
    return templates.TemplateResponse(
        request=request,
        name="auth/login.html",
        context={
            "hospital_name": settings.HOSPITAL_NAME,
            "hospital_address": settings.HOSPITAL_ADDRESS,
            "hospital_phone": settings.HOSPITAL_PHONE
        }
    )


@app.get("/ipd")
async def ipd_dashboard_page(request: Request):
    """IPD Live Status Dashboard"""
    return templates.TemplateResponse(
        request=request,
        name="ipd/dashboard.html",
        context={
            "hospital_name": settings.HOSPITAL_NAME,
            "hospital_address": settings.HOSPITAL_ADDRESS,
            "hospital_phone": settings.HOSPITAL_PHONE
        }
    )


@app.get("/print/{slip_id}")
async def print_slip_page(request: Request, slip_id: str):
    """Universal Printable Slip Page redirecting to printable endpoint"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/api/v1/slips/print/{slip_id}")


@app.get("/patients/register")
async def patient_registration_page(request: Request):
    """Patient registration page"""
    return templates.TemplateResponse(
        request=request,
        name="patients/register.html",
        context={
            "hospital_name": settings.HOSPITAL_NAME,
            "hospital_address": settings.HOSPITAL_ADDRESS,
            "hospital_phone": settings.HOSPITAL_PHONE
        }
    )


@app.get("/patients/{patient_id}")
async def patient_details_page(request: Request, patient_id: str):
    """Patient details page"""
    return templates.TemplateResponse(
        request=request,
        name="patients/details.html",
        context={
            "hospital_name": settings.HOSPITAL_NAME,
            "hospital_address": settings.HOSPITAL_ADDRESS,
            "hospital_phone": settings.HOSPITAL_PHONE,
            "patient_id": patient_id
        }
    )


@app.get("/opd/new")
async def opd_new_page(request: Request):
    """New OPD registration page"""
    return templates.TemplateResponse(
        request=request,
        name="opd/new.html",
        context={
            "hospital_name": settings.HOSPITAL_NAME,
            "hospital_address": settings.HOSPITAL_ADDRESS,
            "hospital_phone": settings.HOSPITAL_PHONE
        }
    )


@app.get("/opd/followup")
async def opd_followup_page(request: Request):
    """OPD follow-up registration page"""
    return templates.TemplateResponse(
        request=request,
        name="opd/followup.html",
        context={
            "hospital_name": settings.HOSPITAL_NAME,
            "hospital_address": settings.HOSPITAL_ADDRESS,
            "hospital_phone": settings.HOSPITAL_PHONE
        }
    )


@app.get("/opd/search")
async def opd_search_page(request: Request):
    """Patient search page"""
    return templates.TemplateResponse(
        request=request,
        name="opd/search.html",
        context={
            "hospital_name": settings.HOSPITAL_NAME,
            "hospital_address": settings.HOSPITAL_ADDRESS,
            "hospital_phone": settings.HOSPITAL_PHONE
        }
    )


@app.get("/ipd/admit")
async def ipd_admit_page(request: Request):
    """IPD admission page"""
    return templates.TemplateResponse(
        request=request,
        name="ipd/admit.html",
        context={
            "hospital_name": settings.HOSPITAL_NAME,
            "hospital_address": settings.HOSPITAL_ADDRESS,
            "hospital_phone": settings.HOSPITAL_PHONE
        }
    )


@app.get("/billing/investigations")
async def billing_investigations_page(request: Request):
    """Billing investigations page"""
    return templates.TemplateResponse(
        request=request,
        name="billing/investigations.html",
        context={
            "hospital_name": settings.HOSPITAL_NAME,
            "hospital_address": settings.HOSPITAL_ADDRESS,
            "hospital_phone": settings.HOSPITAL_PHONE
        }
    )


@app.get("/reports/daily")
async def reports_daily_page(request: Request):
    """Daily reports page"""
    return templates.TemplateResponse(
        request=request,
        name="reports/daily.html",
        context={
            "hospital_name": settings.HOSPITAL_NAME,
            "hospital_address": settings.HOSPITAL_ADDRESS,
            "hospital_phone": settings.HOSPITAL_PHONE
        }
    )


@app.get("/owner")
async def owner_dashboard_page(request: Request):
    """Owner dashboard page (Admin only)"""
    return templates.TemplateResponse(
        request=request,
        name="owner/dashboard.html",
        context={
            "hospital_name": settings.HOSPITAL_NAME,
            "hospital_address": settings.HOSPITAL_ADDRESS,
            "hospital_phone": settings.HOSPITAL_PHONE
        }
    )


@app.get("/owner/employees")
async def owner_employees_page(request: Request):
    """Owner employees management page (Admin only)"""
    return templates.TemplateResponse(
        request=request,
        name="owner/employees.html",
        context={
            "hospital_name": settings.HOSPITAL_NAME,
            "hospital_address": settings.HOSPITAL_ADDRESS,
            "hospital_phone": settings.HOSPITAL_PHONE
        }
    )


@app.get("/owner/salaries")
async def owner_salaries_page(request: Request):
    """Owner salary management page (Admin only)"""
    return templates.TemplateResponse(
        request=request,
        name="owner/salaries.html",
        context={
            "hospital_name": settings.HOSPITAL_NAME,
            "hospital_address": settings.HOSPITAL_ADDRESS,
            "hospital_phone": settings.HOSPITAL_PHONE
        }
    )


@app.get("/owner/doctors")
async def owner_doctors_page(request: Request):
    """Owner doctors management page (Admin only)"""
    return templates.TemplateResponse(
        request=request,
        name="owner/doctors.html",
        context={
            "hospital_name": settings.HOSPITAL_NAME,
            "hospital_address": settings.HOSPITAL_ADDRESS,
            "hospital_phone": settings.HOSPITAL_PHONE
        }
    )


@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint with active database probe"""
    from sqlalchemy import text
    from fastapi.responses import JSONResponse
    
    db_status = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Health check database probe failed: {str(e)}")
        db_status = "unhealthy"
        
    is_healthy = db_status == "healthy"
    status_code = 200 if is_healthy else 503
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if is_healthy else "degraded",
            "database": db_status,
            "service": "Hospital Management System",
            "version": "1.0.0"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.ENVIRONMENT == "development" else False
    )