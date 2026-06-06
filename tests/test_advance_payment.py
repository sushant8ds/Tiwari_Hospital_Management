import pytest
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.payment import payment_crud
from app.crud.patient import patient_crud
from app.crud.ipd import ipd_crud, bed_crud
from app.models.patient import Gender
from app.models.bed import WardType
from app.models.payment import PaymentType


@pytest.mark.asyncio
class TestAdvancePaymentOption:
    """Tests for pay-from-advance functionality"""
    
    async def test_pay_from_advance_workflow(self, db_session: AsyncSession):
        # 1. Create Patient
        patient = await patient_crud.create_patient(
            db=db_session,
            name="Advance Patient",
            age=45,
            gender=Gender.FEMALE,
            address="456 Sector Road",
            mobile_number="9112233445"
        )
        
        # 2. Create Bed and Admit Patient
        bed = await bed_crud.create_bed(
            db=db_session,
            bed_number="BED-ADV1",
            ward_type=WardType.PRIVATE,
            per_day_charge=Decimal("1500.00")
        )
        
        ipd = await ipd_crud.admit_patient(
            db=db_session,
            patient_id=patient.patient_id,
            bed_id=bed.bed_id,
            file_charge=Decimal("500.00")
        )
        
        # 3. Record an initial advance payment (e.g. ₹5,000)
        advance_pay = await payment_crud.record_advance_payment(
            db=db_session,
            ipd_id=ipd.ipd_id,
            amount=Decimal("5000.00"),
            payment_mode="CASH",
            created_by="test_user"
        )
        assert advance_pay is not None
        assert advance_pay.amount == Decimal("5000.00")
        
        # Check initial balance info
        balance_info = await payment_crud.calculate_patient_balance(
            db=db_session,
            patient_id=patient.patient_id,
            ipd_id=ipd.ipd_id
        )
        assert balance_info["advance_balance"] == Decimal("5000.00")
        assert balance_info["total_paid"] == Decimal("5000.00")  # The CASH advance counts as paid
        
        # 4. Pay for an investigation (e.g. ₹1,500) from the advance balance
        investigation_pay = await payment_crud.create_payment(
            db=db_session,
            patient_id=patient.patient_id,
            amount=Decimal("1500.00"),
            payment_mode="ADVANCE",
            payment_type=PaymentType.INVESTIGATION,
            created_by="test_user",
            ipd_id=ipd.ipd_id
        )
        assert investigation_pay is not None
        assert investigation_pay.payment_mode == "ADVANCE"
        assert investigation_pay.amount == Decimal("1500.00")
        
        # 5. Check updated balance info
        # Available advance balance should decrease to ₹3,500
        # Total paid (real money) should stay ₹5,000 (excluding the ADVANCE payment)
        balance_info_after = await payment_crud.calculate_patient_balance(
            db=db_session,
            patient_id=patient.patient_id,
            ipd_id=ipd.ipd_id
        )
        assert balance_info_after["advance_balance"] == Decimal("3500.00")
        assert balance_info_after["total_paid"] == Decimal("5000.00")
        
        # 6. Attempt to pay more than the available advance balance (e.g. ₹4,000)
        # Should raise insufficient balance ValueError
        with pytest.raises(ValueError, match="Insufficient advance balance"):
            await payment_crud.create_payment(
                db=db_session,
                patient_id=patient.patient_id,
                amount=Decimal("4000.00"),
                payment_mode="ADVANCE",
                payment_type=PaymentType.SERVICE,
                created_by="test_user",
                ipd_id=ipd.ipd_id
            )
            
        # 7. Attempt to use ADVANCE payment mode without providing an ipd_id
        # Should raise ValueError indicating pay from advance is only for IPD
        with pytest.raises(ValueError, match="Payment from advance is only allowed for IPD admissions"):
            await payment_crud.create_payment(
                db=db_session,
                patient_id=patient.patient_id,
                amount=Decimal("100.00"),
                payment_mode="ADVANCE",
                payment_type=PaymentType.OPD_FEE,
                created_by="test_user"
            )
