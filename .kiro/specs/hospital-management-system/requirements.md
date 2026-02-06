# Requirements Document

## Introduction

This document specifies the requirements for a comprehensive Hospital OPD-IPD Management Web Application designed for real hospital use in India. The system will manage outpatient department (OPD), inpatient department (IPD), billing, investigations, procedures, services, operation theater (OT), discharge, salary, and employee management with print-ready slips, barcode support, manual charge entry, and offline/online payment handling.

## Glossary

- **Hospital_System**: The complete web-based hospital management application
- **OPD**: Outpatient Department - patients who visit for consultation without admission
- **IPD**: Inpatient Department - patients who are admitted to the hospital
- **Patient_Record**: Complete medical and billing record of a patient
- **Visit_ID**: Unique identifier for each patient visit (OPD or IPD)
- **Barcode_System**: System that generates and prints barcodes on all slips for quick patient identification
- **Manual_Charge**: Custom charges that can be added by authorized users for unlisted services
- **Discharge_Bill**: Final comprehensive bill generated when patient is discharged
- **Reception_User**: User role with access to patient registration, billing, and basic operations
- **Admin_User**: User role with full system access including manual charges and rate editing
- **Thermal_Printer**: Small receipt printer used for printing slips
- **A4_Printer**: Standard paper printer for detailed reports and bills
- **Doctor_Panel**: System module for managing doctor information and consultation fees
- **Serial_Number**: Daily token number that resets each day per doctor
- **Audit_Log**: System record of all manual charge modifications for accountability

## Requirements

### Requirement 1: Patient Registration and Management

**User Story:** As a reception staff member, I want to register new patients and manage follow-up visits, so that I can efficiently handle patient flow and maintain accurate records.

#### Acceptance Criteria

1. WHEN registering a new patient, THE Hospital_System SHALL generate a unique Patient_ID automatically
2. WHEN entering patient details, THE Hospital_System SHALL capture Patient_Name, Age, Gender, Address, and Mobile_Number as mandatory fields
3. WHEN selecting a doctor, THE Hospital_System SHALL provide a dropdown list from the Doctor_Panel
4. WHEN a doctor is selected, THE Hospital_System SHALL auto-fill the corresponding department
5. WHEN processing OPD registration, THE Hospital_System SHALL calculate OPD_Fee and accept payment via Cash, UPI, or Card
6. WHEN registration is complete, THE Hospital_System SHALL print an OPD slip with hospital header, patient details, and barcode containing Patient_ID and Visit_ID
7. WHEN searching for follow-up patients, THE Hospital_System SHALL allow search by Patient_ID or Mobile_Number
8. WHEN a follow-up patient is found, THE Hospital_System SHALL auto-populate patient details and generate a new Serial_Number that resets daily per doctor
9. WHEN processing follow-up visits, THE Hospital_System SHALL calculate follow-up fees and support payment mode selection
10. WHEN generating Visit_ID, THE Hospital_System SHALL ensure global uniqueness and permanent assignment

### Requirement 2: Investigation Management

**User Story:** As a reception staff member, I want to manage patient investigations and generate investigation slips, so that I can coordinate diagnostic services and maintain billing accuracy.

#### Acceptance Criteria

1. WHEN adding investigations to a patient visit, THE Hospital_System SHALL provide options for X-Ray, ECG, Blood_Test, and manual entry
2. WHEN multiple investigations are selected, THE Hospital_System SHALL calculate total charges automatically
3. WHEN manual investigation entry is required, THE Hospital_System SHALL allow custom investigation name and amount entry
4. WHEN investigation charges are processed, THE Hospital_System SHALL link them to the corresponding OPD or IPD visit
5. WHEN investigation slip is generated, THE Hospital_System SHALL include patient details, OPD Visit_Number, investigation list, charges, total, and barcode

### Requirement 3: Procedure and Services Management

**User Story:** As a reception staff member, I want to manage medical procedures and hospital services with accurate billing, so that I can ensure proper charging for all services provided.

#### Acceptance Criteria

1. WHEN recording procedures, THE Hospital_System SHALL support Dressing, Plaster, Suturing, and manual procedure entry
2. WHEN entering procedure details, THE Hospital_System SHALL support quantity input and rate editing by Admin_User
3. WHEN recording services, THE Hospital_System SHALL support Emergency_Bed, hourly bed charges, Oxygen (hourly), Nursing_Care, and manual services
4. WHEN calculating service charges, THE Hospital_System SHALL compute hours automatically from start time to end time
5. WHEN generating procedure or service slips, THE Hospital_System SHALL include patient details, service/procedure list, charges, and barcode
6. WHEN manual charges are required, THE Hospital_System SHALL allow Admin_User to add custom charge names and amounts

### Requirement 4: IPD Management and Bed Allocation

**User Story:** As a reception staff member, I want to convert OPD patients to IPD and manage bed allocation, so that I can efficiently handle patient admissions and track bed occupancy.

#### Acceptance Criteria

1. WHEN converting OPD to IPD, THE Hospital_System SHALL generate a unique IPD_Number automatically
2. WHEN processing IPD admission, THE Hospital_System SHALL charge a one-time file charge and record admission date and time
3. WHEN allocating beds, THE Hospital_System SHALL support Ward_Type selection (General, Semi-Private, Private) with corresponding bed numbers
4. WHEN calculating bed charges, THE Hospital_System SHALL compute per-day charges automatically and maintain bed change history
5. WHEN IPD admission is complete, THE Hospital_System SHALL print an IPD admission slip with patient and admission details

### Requirement 5: Operation Theater Management

**User Story:** As a billing staff member, I want to manage OT charges and generate OT bills, so that I can accurately bill for surgical procedures and related services.

#### Acceptance Criteria

1. WHEN recording OT procedures, THE Hospital_System SHALL capture operation name, date, and duration
2. WHEN entering OT charges, THE Hospital_System SHALL support surgeon charges, anesthesia charges, and OT facility charges
3. WHEN optional assistant charges apply, THE Hospital_System SHALL allow their inclusion in the total
4. WHEN generating OT slips, THE Hospital_System SHALL include patient details, operation details, individual charges, and barcode

### Requirement 6: Discharge and Final Billing

**User Story:** As a billing staff member, I want to generate comprehensive discharge bills, so that I can provide patients with accurate final bills including all services and charges.

#### Acceptance Criteria

1. WHEN generating discharge bills, THE Hospital_System SHALL compile all charges including OPD, IPD bed charges, investigations, procedures, services, OT charges, and manual charges
2. WHEN calculating final amounts, THE Hospital_System SHALL account for advance payments and compute net payable amount
3. WHEN printing discharge bills, THE Hospital_System SHALL include patient details, IPD_Number, itemized charges, total amounts, paid/due status, and barcode
4. WHEN discharge is processed, THE Hospital_System SHALL ensure no billing data is lost and all charges are accurately reflected

### Requirement 7: Barcode System Integration

**User Story:** As a hospital staff member, I want barcode functionality on all slips, so that I can quickly access patient records and improve operational efficiency.

#### Acceptance Criteria

1. WHEN generating any patient slip, THE Hospital_System SHALL print a barcode containing Patient_ID and Visit_ID or IPD_ID
2. WHEN scanning a barcode, THE Hospital_System SHALL open the corresponding patient record instantly
3. WHEN printing slips, THE Hospital_System SHALL ensure barcodes are readable by standard barcode scanners

### Requirement 8: Employee and Salary Management

**User Story:** As an admin user, I want to manage employee records and process salary payments, so that I can maintain staff information and handle payroll efficiently.

#### Acceptance Criteria

1. WHEN adding employees, THE Hospital_System SHALL capture Employee_ID, Name, Post, Qualification, employment status (Permanent/Probation), duty hours, joining date, and monthly salary
2. WHEN generating monthly salaries, THE Hospital_System SHALL create employee-wise salary records
3. WHEN processing salary payments, THE Hospital_System SHALL support advance deductions and generate printable salary slips
4. WHEN managing attendance, THE Hospital_System SHALL provide optional attendance tracking functionality

### Requirement 9: User Role Management and Access Control

**User Story:** As a system administrator, I want to control user access based on roles, so that I can ensure appropriate system security and operational control.

#### Acceptance Criteria

1. WHEN Reception_User logs in, THE Hospital_System SHALL provide access to OPD, follow-up, IPD registration, billing, investigations, procedures, services, and discharge functions
2. WHEN Admin_User logs in, THE Hospital_System SHALL provide full system access including manual charges, doctor panel management, salary processing, reports, and rate editing
3. WHEN any user accesses the system, THE Hospital_System SHALL display hospital logo, name, address, phone, and logged-in user name with role in the header
4. WHEN unauthorized access is attempted, THE Hospital_System SHALL prevent access to restricted functions

### Requirement 10: Printing and Document Generation

**User Story:** As a hospital staff member, I want to print various slips and reports, so that I can provide patients with proper documentation and maintain physical records.

#### Acceptance Criteria

1. WHEN printing slips, THE Hospital_System SHALL support both A4_Printer and Thermal_Printer formats
2. WHEN generating any slip, THE Hospital_System SHALL include hospital header with logo, name, address, and phone number
3. WHEN printing patient documents, THE Hospital_System SHALL ensure all slips contain patient details, relevant charges, and barcodes
4. WHEN reprinting is required, THE Hospital_System SHALL allow authorized users to reprint previous slips from patient visit history

### Requirement 11: Payment Processing

**User Story:** As a reception staff member, I want to process both offline and online payments, so that I can accommodate different patient payment preferences and ensure accurate payment recording.

#### Acceptance Criteria

1. WHEN processing payments, THE Hospital_System SHALL support Cash (offline), UPI, and Card payment modes
2. WHEN recording payments, THE Hospital_System SHALL update patient balances and payment history immediately
3. WHEN handling advance payments, THE Hospital_System SHALL track advance amounts and apply them to final bills
4. WHEN payment processing fails, THE Hospital_System SHALL maintain data integrity and prevent billing errors

### Requirement 12: System Performance and Reliability

**User Story:** As a hospital staff member, I want a fast and reliable system, so that I can efficiently serve patients without technical delays or data loss.

#### Acceptance Criteria

1. WHEN accessing any system function, THE Hospital_System SHALL respond within 2 seconds for normal operations
2. WHEN processing patient data, THE Hospital_System SHALL ensure no data loss occurs during any operation
3. WHEN multiple users access the system simultaneously, THE Hospital_System SHALL maintain performance and data consistency
4. WHEN system errors occur, THE Hospital_System SHALL provide clear error messages and maintain data integrity

### Requirement 13: Search and Patient History

**User Story:** As a hospital staff member, I want to search patient records and view visit history, so that I can quickly access patient information and provide continuity of care.

#### Acceptance Criteria

1. WHEN searching for patients, THE Hospital_System SHALL support search by Patient_ID, Mobile_Number, and Patient_Name
2. WHEN displaying patient history, THE Hospital_System SHALL show date-wise visits, doctors consulted, OPD/IPD status, investigations, procedures, and charges paid
3. WHEN accessing visit history, THE Hospital_System SHALL provide options to reprint previous slips
4. WHEN patient records are accessed, THE Hospital_System SHALL display complete billing and medical service history

### Requirement 14: Manual Charge Entry System

**User Story:** As an admin user, I want to add custom charges for unlisted services, so that I can bill for any hospital service not predefined in the system.

#### Acceptance Criteria

1. WHEN adding manual charges, THE Hospital_System SHALL allow Admin_User to enter custom charge names and amounts
2. WHEN manual charges are added, THE Hospital_System SHALL include them in the patient's final discharge bill
3. WHEN processing manual charges, THE Hospital_System SHALL link them to the appropriate patient visit or IPD record
4. WHEN unauthorized users attempt manual charge entry, THE Hospital_System SHALL restrict access to Admin_User only

### Requirement 15: Reporting and Analytics

**User Story:** As an admin user, I want to generate various reports, so that I can monitor hospital operations, revenue, and staff performance.

#### Acceptance Criteria

1. WHEN generating daily reports, THE Hospital_System SHALL provide OPD patient count and daily collection summaries
2. WHEN analyzing revenue, THE Hospital_System SHALL generate doctor-wise revenue reports and IPD occupancy statistics
3. WHEN processing salary reports, THE Hospital_System SHALL provide comprehensive salary and employee management reports
4. WHEN accessing reports, THE Hospital_System SHALL ensure only Admin_User can view financial and operational analytics

### Requirement 16: Doctor Panel Management

**User Story:** As an admin user, I want to manage doctor information and consultation fees, so that I can maintain accurate doctor records and pricing for the hospital system.

#### Acceptance Criteria

1. WHEN adding doctors, THE Hospital_System SHALL capture Doctor_Name, Department, consultation fees for new and follow-up visits
2. WHEN managing doctor status, THE Hospital_System SHALL support Active and Inactive status settings
3. WHEN doctors are added or updated, THE Hospital_System SHALL populate OPD and follow-up dropdowns dynamically
4. WHEN editing doctor information, THE Hospital_System SHALL restrict access to Admin_User only

### Requirement 17: Slip Format Standardization

**User Story:** As a hospital staff member, I want standardized slip formats, so that all printed documents maintain consistency and include required information.

#### Acceptance Criteria

1. WHEN printing any slip, THE Hospital_System SHALL include hospital logo, name, address, and phone number in the header
2. WHEN generating slips, THE Hospital_System SHALL include slip type (OPD, Investigation, Procedure, Service, OT, Discharge)
3. WHEN printing patient slips, THE Hospital_System SHALL include Patient_Name, Patient_ID, Visit_ID or IPD_ID, date and time
4. WHEN itemizing charges, THE Hospital_System SHALL display itemized charges, total amount, and payment mode
5. WHEN completing slip generation, THE Hospital_System SHALL include barcode and footer note "Please bring this slip for follow-up"

### Requirement 18: Manual Charge Audit System

**User Story:** As a system administrator, I want to track all manual charge modifications, so that I can maintain accountability and audit trails for billing changes.

#### Acceptance Criteria

1. WHEN Admin_User adds manual charges, THE Hospital_System SHALL log user name, date, time, and charge details in Audit_Log
2. WHEN Admin_User edits manual charges, THE Hospital_System SHALL record old value, new value, and modification timestamp
3. WHEN accessing audit logs, THE Hospital_System SHALL restrict access to Admin_User only
4. WHEN generating audit reports, THE Hospital_System SHALL provide comprehensive manual charge modification history

### Requirement 19: Data Backup and Recovery

**User Story:** As a system administrator, I want robust data backup and recovery capabilities, so that I can protect patient and billing data from loss or corruption.

#### Acceptance Criteria

1. WHEN daily operations complete, THE Hospital_System SHALL perform automatic database backup
2. WHEN data export is required, THE Hospital_System SHALL allow Admin_User to export patient and billing data
3. WHEN system failures occur, THE Hospital_System SHALL prevent corruption of patient and billing records
4. WHEN recovery is needed, THE Hospital_System SHALL provide data restoration capabilities from backup files