"""
API endpoints for slip generation and management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import json

from app.core.dependencies import get_db, get_current_user
from app.crud.slip import slip_crud
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


@router.get("/print/opd/{visit_id}")
async def print_opd_slip(
    visit_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Generate printable OPD slip HTML (no authentication required for printing)"""
    from fastapi.responses import HTMLResponse
    from app.crud.visit import visit_crud
    from app.core.config import settings
    from datetime import datetime
    
    try:
        # Get visit details with patient and doctor loaded
        visit = await visit_crud.get_visit_with_details(db, visit_id)
        if not visit:
            raise HTTPException(status_code=404, detail="Visit not found")
        
        # Get patient details
        patient = visit.patient
        doctor = visit.doctor
        
        # Format date
        visit_date = visit.created_date.strftime("%d/%m/%Y")
        
        # Generate HTML slip
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>OPD Slip - {patient.name}</title>
            <style>
                @page {{
                    size: A4;
                    margin: 10mm;
                }}
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 15px;
                    font-size: 11pt;
                }}
                .header-section {{
                    display: flex;
                    align-items: flex-start;
                    border-bottom: 3px solid #8B0000;
                    padding-bottom: 15px;
                    margin-bottom: 20px;
                }}
                .doctor-info {{
                    flex: 0 0 35%;
                    padding-right: 15px;
                }}
                .doctor-name {{
                    font-size: 14pt;
                    font-weight: bold;
                    color: #8B0000;
                    margin-bottom: 5px;
                }}
                .doctor-details {{
                    font-size: 8pt;
                    color: #333;
                    line-height: 1.3;
                    margin: 2px 0;
                }}
                .hospital-info {{
                    flex: 0 0 65%;
                    text-align: center;
                }}
                .logo-container {{
                    margin-bottom: 8px;
                }}
                .logo-container img {{
                    max-width: 70px;
                    max-height: 50px;
                }}
                .hospital-name {{
                    font-size: 22pt;
                    font-weight: bold;
                    color: #8B0000;
                    margin: 5px 0;
                }}
                .hospital-address {{
                    font-size: 9pt;
                    color: #666;
                    line-height: 1.2;
                }}
                .patient-box {{
                    border: 2px solid #000;
                    padding: 12px;
                    margin-bottom: 15px;
                    background: #f9f9f9;
                }}
                .patient-row {{
                    margin: 6px 0;
                    font-size: 10pt;
                }}
                .label {{
                    font-weight: bold;
                    color: #333;
                }}
                .prescription-area {{
                    margin-top: 20px;
                    min-height: 550px;
                    border: 1px dashed #ccc;
                    padding: 15px;
                    background: white;
                }}
                .prescription-header {{
                    font-size: 11pt;
                    font-weight: bold;
                    color: #8B0000;
                    margin-bottom: 15px;
                    padding-bottom: 8px;
                    border-bottom: 1px solid #ddd;
                }}
                .footer {{
                    margin-top: 20px;
                    text-align: center;
                    font-size: 8pt;
                    color: #666;
                    border-top: 1px solid #ddd;
                    padding-top: 8px;
                }}
                @media print {{
                    body {{
                        padding: 0;
                    }}
                    .no-print {{
                        display: none;
                    }}
                    .prescription-area {{
                        border: none;
                    }}
                }}
            </style>
        </head>
        <body>
            <!-- Header Section: Doctor Info (Left) + Hospital Name (Center) -->
            <div class="header-section">
                <div class="doctor-info">
                    <div class="doctor-name">{doctor.name}</div>
                    <div class="doctor-details">M.B.B.S., General Physician</div>
                    <div class="doctor-details">पूर्व चिकित्सक- एम्स (AIIMS) गोरखपुर</div>
                    <div class="doctor-details">(रुद्री, जाड, मोतिहारी एवं नरकटियागंज)</div>
                    <div class="doctor-details" style="margin-top: 5px;">Phone: {settings.HOSPITAL_PHONE}</div>
                    <div class="doctor-details">Email: drnitish{doctor.name.split()[-1].lower()}35@gmail.com</div>
                    <div class="doctor-details" style="color: #8B0000; font-weight: bold; margin-top: 5px; font-size: 7pt;">
                        (सोमवार से शनिवार, दोपहर 02 बजे से शाम 06 बजे तक)
                    </div>
                </div>
                
                <div class="hospital-info">
                    <div class="logo-container">
                        <img src="/static/images/hospital_logo.png" alt="Hospital Logo" onerror="this.style.display='none'">
                    </div>
                    <div class="hospital-name">{settings.HOSPITAL_NAME.upper()}</div>
                    <div class="hospital-address">{settings.HOSPITAL_ADDRESS}</div>
                    <div class="hospital-address">Phone: {settings.HOSPITAL_PHONE}</div>
                </div>
            </div>
            
            <!-- Patient Details -->
            <div class="patient-box">
                <div class="patient-row">
                    <span class="label">Patient Name:</span> {patient.name}
                    <span style="float: right;"><span class="label">Age/Sex:</span> {patient.age}/{patient.gender}</span>
                </div>
                <div class="patient-row">
                    <span class="label">Address:</span> {patient.address or 'N/A'}
                </div>
                <div class="patient-row">
                    <span class="label">Mobile:</span> {patient.mobile_number}
                    <span style="float: right;"><span class="label">Date:</span> {visit_date}</span>
                </div>
                <div class="patient-row">
                    <span class="label">Patient ID:</span> {patient.patient_id}
                    <span style="float: right;"><span class="label">Visit ID:</span> {visit.visit_id}</span>
                </div>
            </div>
            
            <!-- Prescription Area -->
            <div class="prescription-area">
                <div class="prescription-header">Rx (Prescription)</div>
                <!-- Blank space for doctor to write -->
            </div>
            
            <!-- Footer -->
            <div class="footer">
                <p>{settings.HOSPITAL_ADDRESS} | (Not For Medico Legal Purpose)</p>
            </div>
            
            <script>
                // Auto-print when page loads
                window.onload = function() {{
                    window.print();
                }};
            </script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating slip: {str(e)}")


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
