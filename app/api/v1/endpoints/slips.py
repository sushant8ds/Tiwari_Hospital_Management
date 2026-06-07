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
                    border-bottom: 3px solid #1E88E5;
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
                    color: #2C3E50;
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
                    color: #2C3E50;
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
                    color: #2C3E50;
                    margin-bottom: 15px;
                    padding-bottom: 8px;
                    border-bottom: 1px solid #1E88E5;
                }}
                .footer {{
                    margin-top: 20px;
                    text-align: center;
                    font-size: 8pt;
                    color: #666;
                    border-top: 1px solid #ddd;
                    padding-top: 8px;
                }}
                .payment-bank-details {{
                    margin-top: 20px;
                    border: 1px solid #ccc;
                    padding: 10px;
                    background-color: #f9f9f9;
                }}
                .payment-grid {{
                    display: grid;
                    grid-template-columns: 1.2fr 1fr;
                    gap: 15px;
                }}
                .bank-details, .upi-details {{
                    font-size: 9pt;
                }}
                .no-print-banner {{
                    background: #e9ecef;
                    padding: 12px 20px;
                    margin-bottom: 20px;
                    border-radius: 6px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    border: 1px solid #ced4da;
                }}
                .btn-print {{
                    background: #007bff;
                    color: white;
                    border: none;
                    padding: 6px 16px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-weight: bold;
                    margin-right: 10px;
                    font-size: 9.5pt;
                    text-decoration: none;
                    display: inline-flex;
                    align-items: center;
                }}
                .btn-print:hover {{
                    background: #0056b3;
                }}
                .btn-whatsapp {{
                    background: #25d366;
                    color: white;
                    border: none;
                    padding: 6px 16px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-weight: bold;
                    font-size: 9.5pt;
                    text-decoration: none;
                    display: inline-flex;
                    align-items: center;
                }}
                .btn-whatsapp:hover {{
                    background: #1ebd56;
                }}
                @media print {{
                    body {{
                        padding: 0;
                    }}
                    .no-print {{
                        display: none !important;
                    }}
                    .prescription-area {{
                        border: none;
                    }}
                }}
            </style>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
        </head>
        <body>
            <!-- WhatsApp & Print Banner (Hidden on print) -->
            <div class="no-print no-print-banner">
                <span style="font-weight: bold; color: #333; font-size: 10.5pt;">
                    <i class="fas fa-file-medical text-primary" style="margin-right: 6px;"></i>Print Preview - Surya Hospital
                </span>
                <div>
                    <button onclick="window.print()" class="btn-print">
                        <i class="fas fa-print" style="margin-right: 6px;"></i> Print Slip
                    </button>
                    <a id="whatsappShareBtn" href="#" target="_blank" class="btn-whatsapp">
                        <i class="fab fa-whatsapp" style="margin-right: 6px; font-size: 1.1em;"></i> Share via WhatsApp
                    </a>
                </div>
            </div>
            
            <!-- Header Section: Doctor Info (Left) + Hospital Name (Center) -->
            <div class="header-section">
                <div class="doctor-info">
                    <div class="doctor-name">{doctor.name}</div>
                    <div class="doctor-details">M.B.B.S., {doctor.department}</div>
                    <div class="doctor-details">पूर्व चिकित्सक- एम्स (AIIMS) गोरखपुर</div>
                    <div class="doctor-details">(रुद्री, जाड, मोतिहारी एवं नरकटियागंज)</div>
                    <div class="doctor-details" style="margin-top: 5px;">Phone: {settings.HOSPITAL_PHONE}</div>
                    <div class="doctor-details">Email: drnitish{doctor.name.split()[-1].lower()}35@gmail.com</div>
                    <div class="doctor-details" style="color: #2C3E50; font-weight: bold; margin-top: 5px; font-size: 7pt;">
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
                    <span style="float: right;"><span class="label">Age/Sex:</span> {patient.age}/{patient.gender.value if hasattr(patient.gender, 'value') else patient.gender}</span>
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
            
            <!-- Payment & Bank Options -->
            <div class="payment-bank-details">
                <div style="font-weight: bold; color: #2C3E50; border-bottom: 1px solid #1E88E5; margin-bottom: 8px; padding-bottom: 3px; font-size: 9.5pt;">
                    Payment Options & Bank Details
                </div>
                <div class="payment-grid">
                    <div class="bank-details">
                        <strong>Bank Account Transfer (IMPS/NEFT):</strong><br>
                        Bank Name: State Bank of India<br>
                        Account Number: 12345678901<br>
                        IFSC Code: SBIN0001234<br>
                        Account Holder Name: SURYA HOSPITAL
                    </div>
                    <div class="upi-details">
                        <strong>UPI/QR Payment:</strong><br>
                        UPI ID: <span>suryahospital@okaxis</span><br>
                        <div style="margin-top: 5px; font-size: 8.5pt; color: #555;">
                            * You can scan and pay using GPay, PhonePe, Paytm, or any UPI app. Please verify the name <strong>SURYA HOSPITAL</strong> before paying.
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Footer -->
            <div class="footer">
                <p>{settings.HOSPITAL_ADDRESS} | (Not For Medico Legal Purpose)</p>
            </div>
            
            <script>
                document.addEventListener("DOMContentLoaded", function() {{
                    const mobile = "{patient.mobile_number}";
                    const cleanMobile = mobile.replace(/\\D/g, "");
                    const phone = cleanMobile.length === 10 ? "91" + cleanMobile : cleanMobile;
                    const currentUrl = window.location.href;
                    const text = encodeURIComponent("Hello, here is your OPD Slip from Surya Hospital: " + currentUrl);
                    document.getElementById("whatsappShareBtn").href = "https://api.whatsapp.com/send?phone=" + phone + "&text=" + text;
                }});
                
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


@router.get("/print/visit-bill/{visit_id}")
async def print_visit_bill(
    visit_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Generate printable consolidated visit bill HTML (no authentication required for printing)"""
    from fastapi.responses import HTMLResponse
    from app.crud.visit import visit_crud
    from app.core.config import settings
    
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
        
        # Generate charges rows
        charges_rows = ""
        total_amount = float(visit.opd_fee)
        
        # 1. OPD Fee row
        charges_rows += f"""
        <tr>
            <td>1</td>
            <td>OPD Consultation Fee ({visit.visit_type.value if hasattr(visit.visit_type, 'value') else visit.visit_type})</td>
            <td>OPD Fee</td>
            <td>1</td>
            <td>₹{float(visit.opd_fee):.2f}</td>
            <td style="text-align: right;">₹{float(visit.opd_fee):.2f}</td>
        </tr>
        """
        
        # 2. Additional billing charges rows
        for idx, charge in enumerate(visit.billing_charges, start=2):
            total_amount += float(charge.total_amount)
            charges_rows += f"""
            <tr>
                <td>{idx}</td>
                <td>{charge.charge_name}</td>
                <td>{charge.charge_type.value if hasattr(charge.charge_type, 'value') else charge.charge_type}</td>
                <td>{charge.quantity}</td>
                <td>₹{float(charge.rate):.2f}</td>
                <td style="text-align: right;">₹{float(charge.total_amount):.2f}</td>
            </tr>
            """
            
        # Generate HTML slip
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Visit Bill - {patient.name}</title>
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
                    border-bottom: 3px solid #1E88E5;
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
                    color: #2C3E50;
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
                    color: #2C3E50;
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
                .bill-section {{
                    margin-top: 20px;
                    min-height: 450px;
                    border: 1px solid #ddd;
                    padding: 15px;
                    background: white;
                    border-radius: 4px;
                }}
                .bill-header {{
                    font-size: 14pt;
                    font-weight: bold;
                    color: #2C3E50;
                    margin-bottom: 15px;
                    padding-bottom: 8px;
                    border-bottom: 2px solid #1E88E5;
                    text-align: center;
                }}
                .items-table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 10px;
                }}
                .items-table th, .items-table td {{
                    border: 1px solid #ddd;
                    padding: 10px;
                    text-align: left;
                }}
                .items-table th {{
                    background-color: #f5f5f5;
                    font-weight: bold;
                }}
                .total-row {{
                    font-weight: bold;
                    font-size: 1.1em;
                    background-color: #f9f9f9;
                }}
                .footer {{
                    margin-top: 20px;
                    text-align: center;
                    font-size: 8pt;
                    color: #666;
                    border-top: 1px solid #ddd;
                    padding-top: 8px;
                }}
                .payment-bank-details {{
                    margin-top: 20px;
                    border: 1px solid #ccc;
                    padding: 10px;
                    background-color: #f9f9f9;
                }}
                .payment-grid {{
                    display: grid;
                    grid-template-columns: 1.2fr 1fr;
                    gap: 15px;
                }}
                .bank-details, .upi-details {{
                    font-size: 9pt;
                }}
                .no-print-banner {{
                    background: #e9ecef;
                    padding: 12px 20px;
                    margin-bottom: 20px;
                    border-radius: 6px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    border: 1px solid #ced4da;
                }}
                .btn-print {{
                    background: #007bff;
                    color: white;
                    border: none;
                    padding: 6px 16px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-weight: bold;
                    margin-right: 10px;
                    font-size: 9.5pt;
                    text-decoration: none;
                    display: inline-flex;
                    align-items: center;
                }}
                .btn-print:hover {{
                    background: #0056b3;
                }}
                .btn-whatsapp {{
                    background: #25d366;
                    color: white;
                    border: none;
                    padding: 6px 16px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-weight: bold;
                    font-size: 9.5pt;
                    text-decoration: none;
                    display: inline-flex;
                    align-items: center;
                }}
                .btn-whatsapp:hover {{
                    background: #1ebd56;
                }}
                @media print {{
                    body {{
                        padding: 0;
                    }}
                    .no-print {{
                        display: none !important;
                    }}
                }}
            </style>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
        </head>
        <body>
            <!-- WhatsApp & Print Banner (Hidden on print) -->
            <div class="no-print no-print-banner">
                <span style="font-weight: bold; color: #333; font-size: 10.5pt;">
                    <i class="fas fa-file-invoice-dollar text-primary" style="margin-right: 6px;"></i>Print Preview - Surya Hospital Bill
                </span>
                <div>
                    <button onclick="window.print()" class="btn-print">
                        <i class="fas fa-print" style="margin-right: 6px;"></i> Print Bill
                    </button>
                    <a id="whatsappShareBtn" href="#" target="_blank" class="btn-whatsapp">
                        <i class="fab fa-whatsapp" style="margin-right: 6px; font-size: 1.1em;"></i> Share via WhatsApp
                    </a>
                </div>
            </div>
            
            <!-- Header Section: Doctor Info (Left) + Hospital Name (Center) -->
            <div class="header-section">
                <div class="doctor-info">
                    <div class="doctor-name">{doctor.name}</div>
                    <div class="doctor-details">M.B.B.S., {doctor.department}</div>
                    <div class="doctor-details">पूर्व चिकित्सक- एम्स (AIIMS) गोरखपुर</div>
                    <div class="doctor-details">(रुद्री, जाड, मोतिहारी एवं नरकटियागंज)</div>
                    <div class="doctor-details" style="margin-top: 5px;">Phone: {settings.HOSPITAL_PHONE}</div>
                    <div class="doctor-details">Email: drnitish{doctor.name.split()[-1].lower()}35@gmail.com</div>
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
                    <span style="float: right;"><span class="label">Age/Sex:</span> {patient.age}/{patient.gender.value if hasattr(patient.gender, 'value') else patient.gender}</span>
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
            
            <!-- Bill Section -->
            <div class="bill-section">
                <div class="bill-header">OPD VISIT RECEIPT & BILL</div>
                <table class="items-table">
                    <thead>
                        <tr>
                            <th>S.No.</th>
                            <th>Description</th>
                            <th>Category</th>
                            <th>Qty</th>
                            <th>Rate</th>
                            <th style="text-align: right;">Total Amount</th>
                        </tr>
                    </thead>
                    <tbody>
                        {charges_rows}
                        <tr class="total-row">
                            <td colspan="5" style="text-align: right; font-weight: bold;">Grand Total:</td>
                            <td style="text-align: right; font-weight: bold; color: #2C3E50;">₹{total_amount:.2f}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            
            <!-- Payment & Bank Options -->
            <div class="payment-bank-details">
                <div style="font-weight: bold; color: #2C3E50; border-bottom: 1px solid #1E88E5; margin-bottom: 8px; padding-bottom: 3px; font-size: 9.5pt;">
                    Payment Options & Bank Details
                </div>
                <div class="payment-grid">
                    <div class="bank-details">
                        <strong>Bank Account Transfer (IMPS/NEFT):</strong><br>
                        Bank Name: State Bank of India<br>
                        Account Number: 12345678901<br>
                        IFSC Code: SBIN0001234<br>
                        Account Holder Name: SURYA HOSPITAL
                    </div>
                    <div class="upi-details">
                        <strong>UPI/QR Payment:</strong><br>
                        UPI ID: <span>suryahospital@okaxis</span><br>
                        <div style="margin-top: 5px; font-size: 8.5pt; color: #555;">
                            * You can scan and pay using GPay, PhonePe, Paytm, or any UPI app. Please verify the name <strong>SURYA HOSPITAL</strong> before paying.
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Footer -->
            <div class="footer">
                <p>{settings.HOSPITAL_ADDRESS} | (Thank You for Choosing Surya Hospital)</p>
            </div>
            
            <script>
                document.addEventListener("DOMContentLoaded", function() {{
                    const mobile = "{patient.mobile_number}";
                    const cleanMobile = mobile.replace(/\\D/g, "");
                    const phone = cleanMobile.length === 10 ? "91" + cleanMobile : cleanMobile;
                    const currentUrl = window.location.href;
                    const text = encodeURIComponent("Hello, here is your OPD Visit Bill from Surya Hospital: " + currentUrl);
                    document.getElementById("whatsappShareBtn").href = "https://api.whatsapp.com/send?phone=" + phone + "&text=" + text;
                }});
                
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
        raise HTTPException(status_code=500, detail=f"Error generating visit bill: {str(e)}")


@router.get("/print/{slip_id}")
async def print_slip(
    slip_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Generate printable HTML for any slip type (public endpoint)"""
    from fastapi.responses import HTMLResponse
    from app.core.config import settings
    from datetime import datetime
    
    slip = await slip_crud.get_slip_by_id(db, slip_id)
    if not slip:
        raise HTTPException(status_code=404, detail="Slip not found")
        
    content = json.loads(slip.slip_content)
    patient = content.get("patient", {})
    
    # Format generated date
    gen_dt = slip.generated_date
    if not gen_dt:
        try:
            gen_dt = datetime.fromisoformat(content.get("generated_date", ""))
        except:
            gen_dt = datetime.now()
    formatted_date = gen_dt.strftime("%d/%m/%Y %I:%M %p")
    
    slip_type = slip.slip_type.value
    body_html = ""
    
    if slip_type == "OPD":
        visit = content.get("visit", {})
        doctor = content.get("doctor", {})
        charges = content.get("charges", {})
        body_html = f"""
        <div class="info-section">
            <div style="font-weight: bold; font-size: 1.1em; color: #2C3E50; border-bottom: 2px solid #1E88E5; margin-bottom: 10px; padding-bottom: 5px;">
                OPD REGISTRATION SLIP
            </div>
            <table class="data-table">
                <tr>
                    <td class="label">Attending Doctor:</td>
                    <td>Dr. {doctor.get("name", "N/A")} ({doctor.get("department", "N/A")})</td>
                    <td class="label">Serial Number:</td>
                    <td style="font-weight: bold; font-size: 1.2em; color: #2C3E50;">{visit.get("serial_number", "N/A")}</td>
                </tr>
                <tr>
                    <td class="label">Visit ID:</td>
                    <td>{visit.get("id", "N/A")}</td>
                    <td class="label">Visit Type:</td>
                    <td>{visit.get("type", "N/A")}</td>
                </tr>
                <tr>
                    <td class="label">OPD Fee:</td>
                    <td style="font-weight: bold;">₹ {charges.get("opd_fee", 0.0):.2f}</td>
                    <td class="label">Payment Mode:</td>
                    <td>{charges.get("payment_mode", "CASH")}</td>
                </tr>
            </table>
        </div>
        <div class="prescription-area">
            <div class="prescription-header">Rx (Prescription)</div>
        </div>
        """
    elif slip_type == "INVESTIGATION":
        investigations = content.get("investigations", [])
        total_amount = content.get("total_amount", 0.0)
        rows_html = ""
        for idx, inv in enumerate(investigations):
            rows_html += f"""
            <tr>
                <td>{idx+1}</td>
                <td>{inv.get("name", "N/A")}</td>
                <td>{inv.get("quantity", 1)}</td>
                <td style="text-align: right;">₹ {inv.get("rate", 0.0):.2f}</td>
                <td style="text-align: right; font-weight: bold;">₹ {inv.get("total", 0.0):.2f}</td>
            </tr>
            """
        body_html = f"""
        <div class="info-section">
            <div style="font-weight: bold; font-size: 1.1em; color: #2C3E50; border-bottom: 2px solid #1E88E5; margin-bottom: 10px; padding-bottom: 5px;">
                INVESTIGATION RECEIPT
            </div>
            <table class="items-table">
                <thead>
                    <tr>
                        <th style="width: 50px;">S.No.</th>
                        <th>Investigation Name</th>
                        <th style="width: 80px;">Qty</th>
                        <th style="width: 120px; text-align: right;">Rate</th>
                        <th style="width: 120px; text-align: right;">Total</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                    <tr class="total-row">
                        <td colspan="4" style="text-align: right; font-weight: bold;">Grand Total:</td>
                        <td style="text-align: right; font-weight: bold; color: #2C3E50; font-size: 1.1em;">₹ {total_amount:.2f}</td>
                    </tr>
                </tbody>
            </table>
        </div>
        """
    elif slip_type == "PROCEDURE":
        procedures = content.get("procedures", [])
        total_amount = content.get("total_amount", 0.0)
        rows_html = ""
        for idx, proc in enumerate(procedures):
            rows_html += f"""
            <tr>
                <td>{idx+1}</td>
                <td>{proc.get("name", "N/A")}</td>
                <td>{proc.get("quantity", 1)}</td>
                <td style="text-align: right;">₹ {proc.get("rate", 0.0):.2f}</td>
                <td style="text-align: right; font-weight: bold;">₹ {proc.get("total", 0.0):.2f}</td>
            </tr>
            """
        body_html = f"""
        <div class="info-section">
            <div style="font-weight: bold; font-size: 1.1em; color: #2C3E50; border-bottom: 2px solid #1E88E5; margin-bottom: 10px; padding-bottom: 5px;">
                PROCEDURE RECEIPT
            </div>
            <table class="items-table">
                <thead>
                    <tr>
                        <th style="width: 50px;">S.No.</th>
                        <th>Procedure Name</th>
                        <th style="width: 80px;">Qty</th>
                        <th style="width: 120px; text-align: right;">Rate</th>
                        <th style="width: 120px; text-align: right;">Total</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                    <tr class="total-row">
                        <td colspan="4" style="text-align: right; font-weight: bold;">Grand Total:</td>
                        <td style="text-align: right; font-weight: bold; color: #2C3E50; font-size: 1.1em;">₹ {total_amount:.2f}</td>
                    </tr>
                </tbody>
            </table>
        </div>
        """
    elif slip_type == "SERVICE":
        services = content.get("services", [])
        total_amount = content.get("total_amount", 0.0)
        rows_html = ""
        for idx, srv in enumerate(services):
            rows_html += f"""
            <tr>
                <td>{idx+1}</td>
                <td>{srv.get("name", "N/A")}</td>
                <td>{srv.get("quantity", 1)}</td>
                <td style="text-align: right;">₹ {srv.get("rate", 0.0):.2f}</td>
                <td style="text-align: right; font-weight: bold;">₹ {srv.get("total", 0.0):.2f}</td>
            </tr>
            """
        body_html = f"""
        <div class="info-section">
            <div style="font-weight: bold; font-size: 1.1em; color: #2C3E50; border-bottom: 2px solid #1E88E5; margin-bottom: 10px; padding-bottom: 5px;">
                SERVICE CHARGES RECEIPT
            </div>
            <table class="items-table">
                <thead>
                    <tr>
                        <th style="width: 50px;">S.No.</th>
                        <th>Service Name</th>
                        <th style="width: 80px;">Qty</th>
                        <th style="width: 120px; text-align: right;">Rate</th>
                        <th style="width: 120px; text-align: right;">Total</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                    <tr class="total-row">
                        <td colspan="4" style="text-align: right; font-weight: bold;">Grand Total:</td>
                        <td style="text-align: right; font-weight: bold; color: #2C3E50; font-size: 1.1em;">₹ {total_amount:.2f}</td>
                    </tr>
                </tbody>
            </table>
        </div>
        """
    elif slip_type == "OT":
        ot_charges = content.get("ot_charges", [])
        total_amount = content.get("total_amount", 0.0)
        ipd_id = content.get("ipd_id", "N/A")
        rows_html = ""
        for idx, charge in enumerate(ot_charges):
            rows_html += f"""
            <tr>
                <td>{idx+1}</td>
                <td>{charge.get("name", "N/A")}</td>
                <td>{charge.get("quantity", 1)}</td>
                <td style="text-align: right;">₹ {charge.get("rate", 0.0):.2f}</td>
                <td style="text-align: right; font-weight: bold;">₹ {charge.get("total", 0.0):.2f}</td>
            </tr>
            """
        body_html = f"""
        <div class="info-section">
            <div style="font-weight: bold; font-size: 1.1em; color: #2C3E50; border-bottom: 2px solid #1E88E5; margin-bottom: 10px; padding-bottom: 5px;">
                OT BILL & RECEIPT
            </div>
            <div style="margin-bottom: 10px;"><strong>IPD ID:</strong> {ipd_id}</div>
            <table class="items-table">
                <thead>
                    <tr>
                        <th style="width: 50px;">S.No.</th>
                        <th>OT Charge Name</th>
                        <th style="width: 80px;">Qty</th>
                        <th style="width: 120px; text-align: right;">Rate</th>
                        <th style="width: 120px; text-align: right;">Total</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                    <tr class="total-row">
                        <td colspan="4" style="text-align: right; font-weight: bold;">Grand Total:</td>
                        <td style="text-align: right; font-weight: bold; color: #2C3E50; font-size: 1.1em;">₹ {total_amount:.2f}</td>
                    </tr>
                </tbody>
            </table>
        </div>
        """
    elif slip_type == "DISCHARGE":
        ipd = content.get("ipd", {})
        charges_by_type = content.get("charges_by_type", {})
        payments = content.get("payments", [])
        summary = content.get("summary", {})
        
        adm_date_str = ipd.get("admission_date", "")
        dis_date_str = ipd.get("discharge_date", "")
        op_date_str = ipd.get("operation_date", "")
        
        adm_date = datetime.fromisoformat(adm_date_str).strftime("%d/%m/%Y %I:%M %p") if adm_date_str else "N/A"
        dis_date = datetime.fromisoformat(dis_date_str).strftime("%d/%m/%Y %I:%M %p") if dis_date_str else "N/A"
        op_date = datetime.fromisoformat(op_date_str).strftime("%d/%m/%Y") if op_date_str else "N/A"
        
        charges_html = ""
        for ctype, clist in charges_by_type.items():
            charges_html += f"""
            <tr style="background: #eee; font-weight: bold;">
                <td colspan="5">{ctype}</td>
            </tr>
            """
            for idx, c in enumerate(clist):
                charges_html += f"""
                <tr>
                    <td style="padding-left: 15px;">{idx+1}</td>
                    <td>{c.get("name", "N/A")}</td>
                    <td>{c.get("quantity", 1)}</td>
                    <td style="text-align: right;">₹ {c.get("rate", 0.0):.2f}</td>
                    <td style="text-align: right;">₹ {c.get("total", 0.0):.2f}</td>
                </tr>
                """
        
        charges_html += f"""
        <tr style="background: #f2f7fd; font-weight: bold;">
            <td>-</td>
            <td>File Charge (Admission Fee)</td>
            <td>1</td>
            <td style="text-align: right;">₹ {ipd.get("file_charge", 0.0):.2f}</td>
            <td style="text-align: right;">₹ {ipd.get("file_charge", 0.0):.2f}</td>
        </tr>
        """
        
        payments_html = ""
        for idx, p in enumerate(payments):
            pdate = datetime.fromisoformat(p.get("date", "")).strftime("%d/%m/%Y %I:%M %p") if p.get("date") else "N/A"
            payments_html += f"""
            <tr>
                <td>{idx+1}</td>
                <td>{pdate}</td>
                <td>{p.get("type", "N/A").replace("_", " ")}</td>
                <td>{p.get("mode", "N/A")}</td>
                <td style="text-align: right; font-weight: bold;">₹ {p.get("amount", 0.0):.2f}</td>
            </tr>
            """
            
        body_html = f"""
        <div class="info-section">
            <div style="font-weight: bold; font-size: 1.2em; color: #2C3E50; border-bottom: 2px solid #1E88E5; margin-bottom: 15px; padding-bottom: 5px; text-align: center;">
                DISCHARGE SUMMARY & FINAL BILL
            </div>
            
            <h3 style="color: #2C3E50; margin-bottom: 5px;">Admission Details</h3>
            <table class="data-table" style="margin-bottom: 15px;">
                <tr>
                    <td class="label">IPD ID:</td>
                    <td>{ipd.get("id", "N/A")}</td>
                    <td class="label">Attending Doctor:</td>
                    <td>{ipd.get("attending_doctor", "N/A")}</td>
                </tr>
                <tr>
                    <td class="label">Admission Date:</td>
                    <td>{adm_date}</td>
                    <td class="label">Discharge Date:</td>
                    <td>{dis_date}</td>
                </tr>
                <tr>
                    <td class="label">Referred By:</td>
                    <td>{ipd.get("referred_by", "N/A")}</td>
                    <td class="label">Diagnosis:</td>
                    <td style="font-weight: bold; color: #333;">{ipd.get("diagnosis", "N/A")}</td>
                </tr>
                <tr>
                    <td class="label">Procedure:</td>
                    <td>{ipd.get("procedure_performed", "N/A")}</td>
                    <td class="label">Operation Date:</td>
                    <td>{op_date}</td>
                </tr>
            </table>
            
            <h3 style="color: #2C3E50; margin-bottom: 5px;">Detailed Billing Charges</h3>
            <table class="items-table" style="margin-bottom: 15px;">
                <thead>
                    <tr>
                        <th style="width: 50px;">S.No.</th>
                        <th>Charge Description</th>
                        <th style="width: 60px;">Qty/Days</th>
                        <th style="width: 120px; text-align: right;">Rate</th>
                        <th style="width: 120px; text-align: right;">Total Amount</th>
                    </tr>
                </thead>
                <tbody>
                    {charges_html}
                </tbody>
            </table>
            
            <h3 style="color: #2C3E50; margin-bottom: 5px;">Transaction & Advances History</h3>
            <table class="items-table" style="margin-bottom: 15px;">
                <thead>
                    <tr>
                        <th style="width: 50px;">S.No.</th>
                        <th>Payment Date</th>
                        <th>Payment Category</th>
                        <th>Payment Mode</th>
                        <th style="width: 120px; text-align: right;">Paid Amount</th>
                    </tr>
                </thead>
                <tbody>
                    {payments_html}
                </tbody>
            </table>
            
            <div style="display: flex; justify-content: flex-end; margin-top: 15px;">
                <table style="width: 300px; border-collapse: collapse; font-size: 10pt;">
                    <tr>
                        <td style="padding: 5px; font-weight: bold;">Gross Total Charges:</td>
                        <td style="padding: 5px; text-align: right; font-weight: bold;">₹ {summary.get("total_charges", 0.0):.2f}</td>
                    </tr>
                    <tr style="color: green;">
                        <td style="padding: 5px; font-weight: bold;">Discount Offered:</td>
                        <td style="padding: 5px; text-align: right; font-weight: bold;">- ₹ {summary.get("discount", 0.0):.2f}</td>
                    </tr>
                    <tr style="border-top: 1px solid #ddd; font-weight: bold;">
                        <td style="padding: 5px;">Net Billing Amount:</td>
                        <td style="padding: 5px; text-align: right;">₹ {summary.get("net_charges", 0.0):.2f}</td>
                    </tr>
                    <tr style="color: blue;">
                        <td style="padding: 5px; font-weight: bold;">Total Amount Paid:</td>
                        <td style="padding: 5px; text-align: right; font-weight: bold;">- ₹ {summary.get("total_paid", 0.0):.2f}</td>
                    </tr>
                    <tr style="border-top: 2px double #1E88E5; font-size: 1.1em; font-weight: bold; background: #f2f7fd; color: #2C3E50;">
                        <td style="padding: 6px;">Balance Outstanding:</td>
                        <td style="padding: 6px; text-align: right;">₹ {summary.get("balance_due", 0.0):.2f}</td>
                    </tr>
                </table>
            </div>
        </div>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{slip_type} Slip - {patient.get("name", "N/A")}</title>
        <style>
            @page {{
                size: A4;
                margin: 10mm;
            }}
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 15px;
                font-size: 10pt;
                color: #333;
                line-height: 1.4;
            }}
            .header-section {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                border-bottom: 3px solid #1E88E5;
                padding-bottom: 15px;
                margin-bottom: 15px;
            }}
            .hospital-info {{
                flex: 1;
                text-align: center;
            }}
            .hospital-name {{
                font-size: 20pt;
                font-weight: bold;
                color: #2C3E50;
                margin: 2px 0;
            }}
            .hospital-address {{
                font-size: 9pt;
                color: #666;
                margin: 1px 0;
            }}
            .patient-box {{
                border: 2px solid #1E88E5;
                padding: 10px;
                margin-bottom: 15px;
                background: #f2f7fd;
                border-radius: 4px;
            }}
            .patient-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 5px 15px;
            }}
            .patient-row {{
                font-size: 9.5pt;
            }}
            .label {{
                font-weight: bold;
                color: #555;
            }}
            .info-section {{
                margin-top: 15px;
                margin-bottom: 15px;
            }}
            .data-table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 5px;
            }}
            .data-table td {{
                padding: 6px;
                border: 1px solid #ddd;
                font-size: 9.5pt;
            }}
            .items-table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 5px;
            }}
            .items-table th, .items-table td {{
                border: 1px solid #ddd;
                padding: 8px 10px;
                text-align: left;
                font-size: 9.5pt;
            }}
            .items-table th {{
                background-color: #f5f5f5;
                font-weight: bold;
            }}
            .total-row {{
                font-weight: bold;
            }}
            .total-row td {{
                border-top: 2px solid #1E88E5;
            }}
            .prescription-area {{
                margin-top: 20px;
                min-height: 400px;
                border: 1px dashed #ccc;
                padding: 15px;
                background: white;
            }}
            .prescription-header {{
                font-size: 11pt;
                font-weight: bold;
                color: #2C3E50;
                margin-bottom: 15px;
                padding-bottom: 8px;
                border-bottom: 1px solid #1E88E5;
            }}
            .payment-bank-details {{
                margin-top: 20px;
                border: 1px solid #ddd;
                padding: 10px;
                background-color: #fafafa;
                border-radius: 4px;
            }}
            .payment-grid {{
                display: grid;
                grid-template-columns: 1.2fr 1fr;
                gap: 15px;
            }}
            .bank-details, .upi-details {{
                font-size: 9pt;
            }}
            .footer {{
                margin-top: 30px;
                text-align: center;
                font-size: 8pt;
                color: #777;
                border-top: 1px solid #ddd;
                padding-top: 10px;
            }}
            .no-print-banner {{
                background: #e9ecef;
                padding: 12px 20px;
                margin-bottom: 20px;
                border-radius: 6px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                border: 1px solid #ced4da;
            }}
            .btn-print {{
                background: #007bff;
                color: white;
                border: none;
                padding: 6px 16px;
                border-radius: 4px;
                cursor: pointer;
                font-weight: bold;
                margin-right: 10px;
                font-size: 9.5pt;
                text-decoration: none;
                display: inline-flex;
                align-items: center;
            }}
            .btn-print:hover {{
                background: #0056b3;
            }}
            .btn-whatsapp {{
                background: #25d366;
                color: white;
                border: none;
                padding: 6px 16px;
                border-radius: 4px;
                cursor: pointer;
                font-weight: bold;
                font-size: 9.5pt;
                text-decoration: none;
                display: inline-flex;
                align-items: center;
            }}
            .btn-whatsapp:hover {{
                background: #1ebd56;
            }}
            @media print {{
                body {{
                    padding: 0;
                }}
                .no-print {{
                    display: none !important;
                }}
                .prescription-area {{
                    border: none;
                }}
            }}
        </style>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
    </head>
    <body>
        <!-- WhatsApp & Print Banner (Hidden on print) -->
        <div class="no-print no-print-banner">
            <span style="font-weight: bold; color: #333; font-size: 10.5pt;">
                <i class="fas fa-file-medical text-primary" style="margin-right: 6px;"></i>Print Preview - Surya Hospital
            </span>
            <div>
                <button onclick="window.print()" class="btn-print">
                    <i class="fas fa-print" style="margin-right: 6px;"></i> Print Slip
                </button>
                <a id="whatsappShareBtn" href="#" target="_blank" class="btn-whatsapp">
                    <i class="fab fa-whatsapp" style="margin-right: 6px; font-size: 1.1em;"></i> Share via WhatsApp
                </a>
            </div>
        </div>
        
        <!-- Header -->
        <div class="header-section">
            <div style="flex: 0 0 80px;">
                <img src="/static/images/hospital_logo.png" alt="Logo" style="max-height: 60px; max-width: 60px;" onerror="this.style.display='none'">
            </div>
            <div class="hospital-info">
                <div class="hospital-name">{settings.HOSPITAL_NAME.upper()}</div>
                <div class="hospital-address">{settings.HOSPITAL_ADDRESS}</div>
                <div class="hospital-address">Phone: {settings.HOSPITAL_PHONE}</div>
            </div>
            <div style="flex: 0 0 120px; text-align: right; font-size: 8pt; color: #666;">
                <strong>Slip ID:</strong> {slip.slip_id}<br>
                <strong>Format:</strong> {slip.printer_format.value}<br>
                <strong>Date:</strong> {formatted_date}
            </div>
        </div>
        
        <!-- Patient Info -->
        <div class="patient-box">
            <div class="patient-grid">
                <div class="patient-row"><span class="label">Patient Name:</span> {patient.get("name", "N/A")}</div>
                <div class="patient-row"><span class="label">Age / Gender:</span> {patient.get("age", "N/A")} / {patient.get("gender", "N/A")}</div>
                <div class="patient-row"><span class="label">Patient ID:</span> {patient.get("id", "N/A")}</div>
                <div class="patient-row"><span class="label">Mobile:</span> {patient.get("mobile", "N/A")}</div>
                <div class="patient-row" style="grid-column: span 2;"><span class="label">Address:</span> {patient.get("address", "N/A")}</div>
            </div>
        </div>
        
        <!-- Body Details -->
        {body_html}
        
        <!-- Payment & Bank Options -->
        <div class="payment-bank-details">
            <div style="font-weight: bold; color: #2C3E50; border-bottom: 1px solid #1E88E5; margin-bottom: 8px; padding-bottom: 3px; font-size: 9.5pt;">
                Payment Options & Bank Details
            </div>
            <div class="payment-grid">
                <div class="bank-details">
                    <strong>Bank Account Transfer (IMPS/NEFT):</strong><br>
                    Bank Name: State Bank of India<br>
                    Account Number: 12345678901<br>
                    IFSC Code: SBIN0001234<br>
                    Account Holder Name: SURYA HOSPITAL
                </div>
                <div class="upi-details">
                    <strong>UPI/QR Payment:</strong><br>
                    UPI ID: <span>suryahospital@okaxis</span><br>
                    <div style="margin-top: 5px; font-size: 8.5pt; color: #555;">
                        * You can scan and pay using GPay, PhonePe, Paytm, or any UPI app. Please verify the name <strong>SURYA HOSPITAL</strong> before paying.
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <p>{settings.HOSPITAL_ADDRESS} | Phone: {settings.HOSPITAL_PHONE} | (Not For Medico Legal Purpose)</p>
        </div>
        
        <script>
            document.addEventListener("DOMContentLoaded", function() {{
                const mobile = "{patient.get('mobile', '')}";
                const cleanMobile = mobile.replace(/\\D/g, "");
                const phone = cleanMobile.length === 10 ? "91" + cleanMobile : cleanMobile;
                const currentUrl = window.location.href;
                const text = encodeURIComponent("Hello, here is your medical slip from Surya Hospital: " + currentUrl);
                document.getElementById("whatsappShareBtn").href = "https://api.whatsapp.com/send?phone=" + phone + "&text=" + text;
            }});
            
            window.onload = function() {{
                window.print();
            }};
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


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
