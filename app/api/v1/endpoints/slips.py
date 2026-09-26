"""
API endpoints for slip generation, printing, and management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime
import json

from app.core.dependencies import get_db, get_current_user
from app.core.config import settings
from app.core.templates import templates
from app.crud.slip import slip_crud
from app.crud.visit import visit_crud
from app.crud.patient import patient_crud
from app.services.barcode_service import barcode_service
from app.models.billing import ChargeType
from app.schemas.slip import (
    SlipGenerateRequest,
    SlipReprintRequest,
    SlipResponse,
    SlipContentResponse,
    PrinterFormatEnum
)
from app.models.slip import PrinterFormat
from app.models.user import User

router = APIRouter()


@router.post("/generate/opd/{visit_id}", response_model=SlipContentResponse)
async def generate_opd_slip(
    visit_id: str,
    printer_format: PrinterFormatEnum = PrinterFormatEnum.A4,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate OPD slip"""
    try:
        slip = await slip_crud.generate_opd_slip(
            db=db,
            visit_id=visit_id,
            printer_format=PrinterFormat[printer_format.value],
            generated_by=current_user.user_id
        )
        
        return SlipContentResponse(
            slip_id=slip.slip_id,
            patient_id=slip.patient_id,
            slip_type=slip.slip_type.value,
            barcode_data=slip.barcode_data,
            barcode_image=slip.barcode_image,
            content=json.loads(slip.slip_content),
            printer_format=slip.printer_format.value,
            generated_date=slip.generated_date
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/print/opd/{visit_id}", response_class=HTMLResponse)
async def print_opd_slip(
    request: Request,
    visit_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Generate printable OPD slip HTML rendered via Jinja2 template with dynamic Patient & Diagnostic QR Code"""
    try:
        visit = await visit_crud.get_visit_with_details(db, visit_id)
        if not visit:
            raise HTTPException(status_code=404, detail="Visit not found")
        
        visit_date = visit.created_date.strftime("%d/%m/%Y") if visit.created_date else datetime.now().strftime("%d/%m/%Y")
        
        # Retrieve full patient history including all visits, IPD admissions, and billing charges
        patient_history = await patient_crud.get_patient_history(db, visit.patient_id)
        
        # Collect all diagnostics, investigations, procedures, and tests done
        investigations_done = []
        if patient_history:
            # Check all visits
            for v in (patient_history.visits or []):
                v_date = v.visit_date.strftime("%d/%m/%Y") if v.visit_date else "N/A"
                for c in (v.billing_charges or []):
                    if c.charge_type in (ChargeType.INVESTIGATION, ChargeType.PROCEDURE, ChargeType.SERVICE):
                        investigations_done.append(f"{c.charge_name} ({v_date})")
            
            # Check IPD admissions
            for ipd in (patient_history.ipd_admissions or []):
                ipd_date = ipd.admission_date.strftime("%d/%m/%Y") if ipd.admission_date else "N/A"
                for c in (ipd.billing_charges or []):
                    if c.charge_type in (ChargeType.INVESTIGATION, ChargeType.PROCEDURE, ChargeType.SERVICE):
                        investigations_done.append(f"{c.charge_name} [IPD] ({ipd_date})")
        
        # Deduplicate and sort/format
        investigations_summary = ", ".join(investigations_done) if investigations_done else "None recorded"
        
        gender_str = visit.patient.gender.value if hasattr(visit.patient.gender, 'value') else str(visit.patient.gender)
        doctor_name = visit.doctor.name if visit.doctor else "Medical Officer"
        doctor_dept = visit.doctor.department if visit.doctor else visit.department or "General Medicine"

        # Build clean QR payload with full patient dossier & diagnostic records
        qr_lines = [
            f"=== {settings.HOSPITAL_NAME.upper()} ===",
            f"PATIENT ID: {visit.patient.patient_id}",
            f"NAME: {visit.patient.name}",
            f"AGE/SEX: {visit.patient.age} / {gender_str}",
            f"MOBILE: {visit.patient.mobile_number}",
            f"ADDRESS: {visit.patient.address or 'N/A'}",
            f"--- CURRENT VISIT ---",
            f"VISIT ID: {visit.visit_id}",
            f"DATE: {visit_date}",
            f"DOCTOR: {doctor_name} ({doctor_dept})",
            f"--- DIAGNOSTICS & TESTS RECORD ---",
            f"INVESTIGATIONS DONE: {investigations_summary}",
            f"==========================",
            f"Helpline: {settings.HOSPITAL_PHONE}"
        ]
        qr_text = "\n".join(qr_lines)
        
        # Generate QR code image base64
        qr_code_image = barcode_service.generate_qr_code(qr_text, box_size=4, border=2)
        
        return templates.TemplateResponse(
            request=request,
            name="slips/opd_slip.html",
            context={
                "visit": visit,
                "patient": visit.patient,
                "doctor": visit.doctor,
                "visit_date": visit_date,
                "hospital_name": settings.HOSPITAL_NAME,
                "hospital_address": settings.HOSPITAL_ADDRESS,
                "hospital_phone": settings.HOSPITAL_PHONE,
                "qr_code_image": qr_code_image,
                "investigations_done": investigations_done
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating OPD slip: {str(e)}")


@router.get("/print/visit-bill/{visit_id}", response_class=HTMLResponse)
async def print_visit_bill(
    request: Request,
    visit_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Generate printable consolidated visit bill HTML rendered via Jinja2 template"""
    try:
        visit = await visit_crud.get_visit_with_details(db, visit_id)
        if not visit:
            raise HTTPException(status_code=404, detail="Visit not found")
        
        visit_date = visit.created_date.strftime("%d/%m/%Y") if visit.created_date else datetime.now().strftime("%d/%m/%Y")
        total_amount = float(visit.opd_fee)
        charges = list(visit.billing_charges) if visit.billing_charges else []
        for charge in charges:
            total_amount += float(charge.total_amount)
            
        return templates.TemplateResponse(
            request=request,
            name="slips/visit_bill.html",
            context={
                "visit": visit,
                "patient": visit.patient,
                "doctor": visit.doctor,
                "charges": charges,
                "visit_date": visit_date,
                "total_amount": total_amount,
                "hospital_name": settings.HOSPITAL_NAME,
                "hospital_address": settings.HOSPITAL_ADDRESS,
                "hospital_phone": settings.HOSPITAL_PHONE
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating visit bill: {str(e)}")


@router.get("/print/discharge-summary/{ipd_id}", response_class=HTMLResponse)
async def print_discharge_summary(
    request: Request,
    ipd_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Generate printable clinical Discharge Summary PDF/HTML matching sample format"""
    try:
        from app.crud.ipd import ipd_crud
        from datetime import timedelta
        
        ipd = await ipd_crud.get_ipd_by_id(db, ipd_id)
        if not ipd:
            raise HTTPException(status_code=404, detail="IPD record not found")
        
        admission_date_formatted = ipd.admission_date.strftime("%d-%b-%Y, %I:%M %p") if ipd.admission_date else datetime.now().strftime("%d-%b-%Y, %I:%M %p")
        discharge_date_formatted = ipd.discharge_date.strftime("%d-%b-%Y, %I:%M %p") if ipd.discharge_date else datetime.now().strftime("%d-%b-%Y, %I:%M %p")
        operation_date_formatted = ipd.operation_date.strftime("%d-%b-%Y") if ipd.operation_date else (ipd.admission_date.strftime("%d-%b-%Y") if ipd.admission_date else datetime.now().strftime("%d-%b-%Y"))
        
        follow_up_dt = (ipd.discharge_date or datetime.now()) + timedelta(days=5)
        follow_up_date_formatted = follow_up_dt.strftime("%d-%b-%Y (%A)")
        
        return templates.TemplateResponse(
            request=request,
            name="slips/discharge_summary.html",
            context={
                "ipd": ipd,
                "patient": ipd.patient,
                "doctor": ipd.attending_doctor,
                "admission_date_formatted": admission_date_formatted,
                "discharge_date_formatted": discharge_date_formatted,
                "operation_date_formatted": operation_date_formatted,
                "follow_up_date_formatted": follow_up_date_formatted,
                "hospital_name": settings.HOSPITAL_NAME,
                "hospital_address": settings.HOSPITAL_ADDRESS,
                "hospital_phone": settings.HOSPITAL_PHONE
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating discharge summary: {str(e)}")


@router.get("/print/{slip_id}", response_class=HTMLResponse)
async def print_slip(
    request: Request,
    slip_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Generate printable HTML for any slip type rendered via Jinja2 template"""
    slip = await slip_crud.get_slip_by_id(db, slip_id)
    if not slip:
        raise HTTPException(status_code=404, detail="Slip not found")
        
    content = json.loads(slip.slip_content)
    patient = content.get("patient", {})
    
    # If this is a DISCHARGE slip and has an ipd_id, render the comprehensive Discharge Summary
    if slip.slip_type == SlipType.DISCHARGE and slip.ipd_id:
        from app.crud.ipd import ipd_crud
        from datetime import timedelta
        ipd = await ipd_crud.get_ipd_by_id(db, slip.ipd_id)
        if ipd:
            admission_date_formatted = ipd.admission_date.strftime("%d-%b-%Y, %I:%M %p") if ipd.admission_date else datetime.now().strftime("%d-%b-%Y, %I:%M %p")
            discharge_date_formatted = ipd.discharge_date.strftime("%d-%b-%Y, %I:%M %p") if ipd.discharge_date else datetime.now().strftime("%d-%b-%Y, %I:%M %p")
            operation_date_formatted = ipd.operation_date.strftime("%d-%b-%Y") if ipd.operation_date else (ipd.admission_date.strftime("%d-%b-%Y") if ipd.admission_date else datetime.now().strftime("%d-%b-%Y"))
            follow_up_dt = (ipd.discharge_date or datetime.now()) + timedelta(days=5)
            follow_up_date_formatted = follow_up_dt.strftime("%d-%b-%Y (%A)")
            
            return templates.TemplateResponse(
                request=request,
                name="slips/discharge_summary.html",
                context={
                    "ipd": ipd,
                    "patient": ipd.patient,
                    "doctor": ipd.attending_doctor,
                    "admission_date_formatted": admission_date_formatted,
                    "discharge_date_formatted": discharge_date_formatted,
                    "operation_date_formatted": operation_date_formatted,
                    "follow_up_date_formatted": follow_up_date_formatted,
                    "hospital_name": settings.HOSPITAL_NAME,
                    "hospital_address": settings.HOSPITAL_ADDRESS,
                    "hospital_phone": settings.HOSPITAL_PHONE
                }
            )

    gen_dt = slip.generated_date
    if not gen_dt:
        try:
            gen_dt = datetime.fromisoformat(content.get("generated_date", ""))
        except Exception:
            gen_dt = datetime.now()
    formatted_date = gen_dt.strftime("%d/%m/%Y %I:%M %p")
    
    return templates.TemplateResponse(
        request=request,
        name="slips/universal_slip.html",
        context={
            "slip": slip,
            "content": content,
            "patient": patient,
            "slip_type": slip.slip_type.value,
            "formatted_date": formatted_date,
            "hospital_name": settings.HOSPITAL_NAME,
            "hospital_address": settings.HOSPITAL_ADDRESS,
            "hospital_phone": settings.HOSPITAL_PHONE
        }
    )


@router.post("/generate/investigation", response_model=SlipContentResponse)
async def generate_investigation_slip(
    visit_id: str = None,
    ipd_id: str = None,
    printer_format: PrinterFormatEnum = PrinterFormatEnum.A4,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate investigation slip"""
    try:
        slip = await slip_crud.generate_investigation_slip(
            db=db,
            visit_id=visit_id,
            ipd_id=ipd_id,
            printer_format=PrinterFormat[printer_format.value],
            generated_by=current_user.user_id
        )
        
        return SlipContentResponse(
            slip_id=slip.slip_id,
            patient_id=slip.patient_id,
            slip_type=slip.slip_type.value,
            barcode_data=slip.barcode_data,
            barcode_image=slip.barcode_image,
            content=json.loads(slip.slip_content),
            printer_format=slip.printer_format.value,
            generated_date=slip.generated_date
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/generate/procedure", response_model=SlipContentResponse)
async def generate_procedure_slip(
    visit_id: str = None,
    ipd_id: str = None,
    printer_format: PrinterFormatEnum = PrinterFormatEnum.A4,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate procedure slip"""
    try:
        slip = await slip_crud.generate_procedure_slip(
            db=db,
            visit_id=visit_id,
            ipd_id=ipd_id,
            printer_format=PrinterFormat[printer_format.value],
            generated_by=current_user.user_id
        )
        
        return SlipContentResponse(
            slip_id=slip.slip_id,
            patient_id=slip.patient_id,
            slip_type=slip.slip_type.value,
            barcode_data=slip.barcode_data,
            barcode_image=slip.barcode_image,
            content=json.loads(slip.slip_content),
            printer_format=slip.printer_format.value,
            generated_date=slip.generated_date
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/generate/service", response_model=SlipContentResponse)
async def generate_service_slip(
    visit_id: str = None,
    ipd_id: str = None,
    printer_format: PrinterFormatEnum = PrinterFormatEnum.A4,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate service slip"""
    try:
        slip = await slip_crud.generate_service_slip(
            db=db,
            visit_id=visit_id,
            ipd_id=ipd_id,
            printer_format=PrinterFormat[printer_format.value],
            generated_by=current_user.user_id
        )
        
        return SlipContentResponse(
            slip_id=slip.slip_id,
            patient_id=slip.patient_id,
            slip_type=slip.slip_type.value,
            barcode_data=slip.barcode_data,
            barcode_image=slip.barcode_image,
            content=json.loads(slip.slip_content),
            printer_format=slip.printer_format.value,
            generated_date=slip.generated_date
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/generate/ot/{ipd_id}", response_model=SlipContentResponse)
async def generate_ot_slip(
    ipd_id: str,
    printer_format: PrinterFormatEnum = PrinterFormatEnum.A4,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate OT slip"""
    try:
        slip = await slip_crud.generate_ot_slip(
            db=db,
            ipd_id=ipd_id,
            printer_format=PrinterFormat[printer_format.value],
            generated_by=current_user.user_id
        )
        
        return SlipContentResponse(
            slip_id=slip.slip_id,
            patient_id=slip.patient_id,
            slip_type=slip.slip_type.value,
            barcode_data=slip.barcode_data,
            barcode_image=slip.barcode_image,
            content=json.loads(slip.slip_content),
            printer_format=slip.printer_format.value,
            generated_date=slip.generated_date
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/generate/discharge/{ipd_id}", response_model=SlipContentResponse)
async def generate_discharge_slip(
    ipd_id: str,
    printer_format: PrinterFormatEnum = PrinterFormatEnum.A4,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate discharge slip"""
    try:
        slip = await slip_crud.generate_discharge_slip(
            db=db,
            ipd_id=ipd_id,
            printer_format=PrinterFormat[printer_format.value],
            generated_by=current_user.user_id
        )
        
        return SlipContentResponse(
            slip_id=slip.slip_id,
            patient_id=slip.patient_id,
            slip_type=slip.slip_type.value,
            barcode_data=slip.barcode_data,
            barcode_image=slip.barcode_image,
            content=json.loads(slip.slip_content),
            printer_format=slip.printer_format.value,
            generated_date=slip.generated_date
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/reprint/{slip_id}", response_model=SlipContentResponse)
async def reprint_slip(
    slip_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reprint an existing slip"""
    try:
        slip = await slip_crud.reprint_slip(
            db=db,
            original_slip_id=slip_id,
            generated_by=current_user.user_id
        )
        
        return SlipContentResponse(
            slip_id=slip.slip_id,
            patient_id=slip.patient_id,
            slip_type=slip.slip_type.value,
            barcode_data=slip.barcode_data,
            barcode_image=slip.barcode_image,
            content=json.loads(slip.slip_content),
            printer_format=slip.printer_format.value,
            generated_date=slip.generated_date
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{slip_id}", response_model=SlipContentResponse)
async def get_slip(
    slip_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get slip by ID"""
    slip = await slip_crud.get_slip_by_id(db, slip_id)
    if not slip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slip not found")
    
    return SlipContentResponse(
        slip_id=slip.slip_id,
        patient_id=slip.patient_id,
        slip_type=slip.slip_type.value,
        barcode_data=slip.barcode_data,
        barcode_image=slip.barcode_image,
        content=json.loads(slip.slip_content),
        printer_format=slip.printer_format.value,
        generated_date=slip.generated_date
    )


@router.get("/patient/{patient_id}", response_model=List[SlipResponse])
async def get_patient_slips(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all slips for a patient"""
    slips = await slip_crud.get_slips_by_patient(db, patient_id)
    return slips


@router.get("/visit/{visit_id}", response_model=List[SlipResponse])
async def get_visit_slips(
    visit_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all slips for a visit"""
    slips = await slip_crud.get_slips_by_visit(db, visit_id)
    return slips


@router.get("/ipd/{ipd_id}", response_model=List[SlipResponse])
async def get_ipd_slips(
    ipd_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all slips for an IPD admission"""
    slips = await slip_crud.get_slips_by_ipd(db, ipd_id)
    return slips
