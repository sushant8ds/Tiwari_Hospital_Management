"""
Barcode generation service
"""

import barcode
from barcode.writer import ImageWriter
import qrcode
from io import BytesIO
import base64
from datetime import datetime


class BarcodeService:
    """Service for generating barcodes and QR codes"""
    
    @staticmethod
    def generate_barcode_data(patient_id: str, visit_or_ipd_id: str) -> str:
        """Generate barcode data string"""
        timestamp = str(int(datetime.now().timestamp()))
        return f"{patient_id}-{visit_or_ipd_id}-{timestamp}"
    
    @staticmethod
    def generate_barcode_image(data: str, format: str = "code128") -> str:
        """Generate barcode image and return as base64 string"""
        try:
            # Create barcode
            barcode_class = barcode.get_barcode_class(format)
            barcode_instance = barcode_class(data, writer=ImageWriter())
            
            # Generate image
            buffer = BytesIO()
            barcode_instance.write(buffer)
            buffer.seek(0)
            
            # Convert to base64
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            return f"data:image/png;base64,{image_base64}"
            
        except Exception as e:
            print(f"Error generating barcode: {e}")
            return ""
    
    @staticmethod
    def generate_qr_code(data: str) -> str:
        """Generate QR code and return as base64 string"""
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            return f"data:image/png;base64,{image_base64}"
            
        except Exception as e:
            print(f"Error generating QR code: {e}")
            return ""


# Global barcode service instance
barcode_service = BarcodeService()