# Implementation Plan: Hospital OPD-IPD Management System

## Overview

This implementation plan breaks down the Hospital Management System into discrete coding tasks using Python. The system will be built as a web application using FastAPI (preferred over Flask) for the backend, SQLAlchemy for database operations, and a modern frontend framework. Each task builds incrementally toward a complete hospital management solution.

## Tasks

- [x] 1. Set up project structure and core infrastructure
  - Create Python project structure with virtual environment
  - Set up FastAPI application with basic configuration
  - Configure SQLAlchemy database connection and models
  - Set up Alembic for database migrations
  - Create base templates and static file structure
  - _Requirements: 9.1, 9.2, 12.1_

- [ ] 2. Implement user authentication and role-based access control
  - [x] 2.1 Create User model and authentication system
    - Implement User model with role-based permissions
    - Create login/logout functionality with session management
    - Implement role-based decorators for route protection
    - _Requirements: 9.1, 9.2, 9.3, 9.4_
  
  - [x] 2.2 Write property test for role-based access control
    - **Property 3: Role-Based Access Control**
    - **Validates: Requirements 3.2, 3.6, 9.1, 9.2, 9.4, 10.4, 14.4, 15.4, 16.4, 18.3**

- [ ] 3. Implement core database models and validation
  - [x] 3.1 Create Patient, Doctor, and Visit models
    - Implement Patient model with validation for required fields
    - Implement Doctor model with department and fee management
    - Implement Visit model with unique ID generation and serial number logic
    - _Requirements: 1.1, 1.2, 16.1_
  
  - [x] 3.2 Write property test for unique ID generation
    - **Property 1: Unique ID Generation**
    - **Validates: Requirements 1.1, 1.10, 4.1**
  
  - [x] 3.3 Write property test for required field validation
    - **Property 2: Required Field Validation**
    - **Validates: Requirements 1.2, 8.1, 16.1**

- [ ] 4. Implement patient registration and search functionality
  - [x] 4.1 Create patient registration endpoints and forms
    - Implement new patient registration with validation
    - Create patient search functionality by ID, mobile, and name
    - Implement patient details update functionality
    - _Requirements: 1.1, 1.2, 1.7, 13.1_
  
  - [x] 4.2 Write property test for search functionality
    - **Property 10: Search Functionality Completeness**
    - **Validates: Requirements 1.7, 13.1**

- [ ] 5. Implement OPD management system
  - [x] 5.1 Create OPD registration and follow-up functionality
    - Implement new OPD patient registration with doctor selection
    - Implement follow-up patient registration with serial number generation
    - Create doctor-department auto-fill functionality
    - _Requirements: 1.3, 1.4, 1.5, 1.8, 1.9_
  
  - [x] 5.2 Write property test for doctor-department consistency
    - **Property 4: Doctor-Department Consistency**
    - **Validates: Requirements 1.4**
  
  - [x] 5.3 Write property test for serial number daily reset
    - **Property 5: Serial Number Daily Reset**
    - **Validates: Requirements 1.8**

- [ ] 6. Implement billing and charges management
  - [x] 6.1 Create billing models and charge calculation system
    - Implement BillingCharges model for all charge types
    - Create investigation charges functionality
    - Create procedure charges functionality
    - Create service charges with time calculation
    - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.3, 3.4_
  
  - [x] 6.2 Write property test for charge calculation accuracy
    - **Property 7: Charge Calculation Accuracy**
    - **Validates: Requirements 2.2, 3.4, 6.1, 6.2**
  
  - [x] 6.3 Write property test for data linkage integrity
    - **Property 8: Data Linkage Integrity**
    - **Validates: Requirements 2.4, 14.3**

- [x] 7. Checkpoint - Ensure core functionality works
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 8. Implement IPD management and bed allocation
  - [x] 8.1 Create IPD models and admission functionality
    - Implement IPD model with unique ID generation
    - Create OPD to IPD conversion functionality
    - Implement bed allocation system with ward types
    - Create bed change history tracking
    - _Requirements: 4.1, 4.2, 4.3, 4.4_
  
  - [x] 8.2 Write property test for bed allocation consistency
    - **Property 13: Bed Allocation Consistency**
    - **Validates: Requirements 4.3, 4.4**

- [ ] 9. Implement Operation Theater management
  - [x] 9.1 Create OT charges and procedure tracking
    - Implement OT procedure recording functionality
    - Create OT charges calculation (surgeon, anesthesia, facility)
    - Implement optional assistant charges
    - _Requirements: 5.1, 5.2, 5.3_

- [ ] 10. Implement payment processing system
  - [x] 10.1 Create payment processing and tracking
    - Implement payment mode support (Cash, UPI, Card)
    - Create advance payment tracking system
    - Implement immediate balance updates
    - Create payment history tracking
    - _Requirements: 11.1, 11.2, 11.3, 11.4_
  
  - [x] 10.2 Write property test for payment mode support
    - **Property 9: Payment Mode Support**
    - **Validates: Requirements 1.5, 11.1**
  
  - [x] 10.3 Write property test for payment recording immediacy
    - **Property 21: Payment Recording Immediacy**
    - **Validates: Requirements 11.2**

- [ ] 11. Implement slip generation and barcode system
  - [x] 11.1 Create slip generation system
    - Implement slip templates for all types (OPD, Investigation, Procedure, Service, OT, Discharge)
    - Create barcode generation functionality
    - Implement printer format support (A4 and thermal)
    - Create slip reprinting functionality
    - _Requirements: 1.6, 2.5, 3.5, 4.5, 5.4, 7.1, 10.1, 17.1, 17.2, 17.3, 17.4, 17.5_
  
  - [x] 11.2 Write property test for comprehensive slip content validation
    - **Property 6: Comprehensive Slip Content Validation**
    - **Validates: Requirements 1.6, 2.5, 3.5, 4.5, 5.4, 6.3, 10.2, 10.3, 17.1, 17.2, 17.3, 17.4, 17.5**
  
  - [x] 11.3 Write property test for barcode content validation
    - **Property 11: Barcode Content Validation**
    - **Validates: Requirements 7.1**
  
  - [x] 11.4 Write property test for barcode-record mapping
    - **Property 12: Barcode-Record Mapping**
    - **Validates: Requirements 7.2**

- [ ] 12. Implement discharge and final billing system
  - [x] 12.1 Create discharge bill generation
    - Implement comprehensive discharge bill compilation
    - Create advance payment application logic
    - Implement final bill generation with all charge types
    - Create discharge processing workflow
    - _Requirements: 6.1, 6.2, 6.3, 6.4_
  
  - [x] 12.2 Write property test for discharge bill completeness
    - **Property 15: Discharge Bill Completeness**
    - **Validates: Requirements 6.1**
  
  - [x] 12.3 Write property test for advance payment application
    - **Property 16: Advance Payment Application**
    - **Validates: Requirements 6.2, 11.3**

- [ ] 13. Implement manual charges and audit system
  - [x] 13.1 Create manual charge entry system
    - Implement manual charge addition for Admin users
    - Create manual charge editing functionality
    - Implement audit logging for all manual charge operations
    - Create audit report generation
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 18.1, 18.2, 18.3, 18.4_
  
  - [x] 13.2 Write property test for audit trail completeness
    - **Property 18: Audit Trail Completeness**
    - **Validates: Requirements 18.1, 18.2**

- [ ] 14. Implement employee and salary management
  - [x] 14.1 Create employee management system
    - Implement Employee model with all required fields
    - Create employee registration and management functionality
    - Implement salary processing and slip generation
    - Create optional attendance tracking
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ] 15. Implement patient history and reporting
  - [x] 15.1 Create patient history and reporting system
    - Implement comprehensive patient history display
    - Create daily reports (OPD count, collections)
    - Create doctor-wise revenue reports
    - Create IPD occupancy reports
    - Implement salary reports
    - _Requirements: 13.2, 13.3, 13.4, 15.1, 15.2, 15.3, 15.4_
  
  - [x] 15.2 Write property test for patient history completeness
    - **Property 19: Patient History Completeness**
    - **Validates: Requirements 13.2, 13.4**

- [ ] 16. Implement data backup and recovery system
  - [x] 16.1 Create backup and recovery functionality
    - Implement automatic daily database backup
    - Create data export functionality for Admin users
    - Implement data restoration capabilities
    - Create backup integrity validation
    - Set up schema migration strategy using Alembic
    - _Requirements: 19.1, 19.2, 19.3, 19.4_
  
  - [x] 16.2 Write property test for backup creation consistency
    - **Property 22: Backup Creation Consistency**
    - **Validates: Requirements 19.1**
  
  - [x] 16.3 Write property test for data export completeness
    - **Property 23: Data Export Completeness**
    - **Validates: Requirements 19.2**

- [ ] 17. Implement frontend user interface
  - [x] 17.1 Create responsive web interface
    - Implement patient registration forms
    - Create OPD and IPD management interfaces
    - Implement billing and charges interfaces
    - Create reporting dashboards
    - Implement barcode scanning interface
    - _Requirements: 9.3, 10.2, 10.3_

- [ ] 18. Integration and final testing
  - [x] 18.1 Integrate all components and test end-to-end workflows
    - Wire all components together
    - Test complete patient journey from registration to discharge
    - Implement error handling and validation
    - Test printer integration and barcode scanning
    - _Requirements: 12.2, 12.4_
  
  - [x] 18.2 Write integration tests for complete workflows
    - Test OPD registration to discharge workflow
    - Test IPD admission to discharge workflow
    - Test payment processing and slip generation
    - _Requirements: 6.4, 11.4, 12.2_

- [x] 19. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- All tasks are required for comprehensive hospital management system
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties using Python's Hypothesis library
- Unit tests validate specific examples and edge cases
- The system uses Python with FastAPI, SQLAlchemy, and modern web technologies
- All property tests should run minimum 100 iterations
- Each property test must be tagged with: **Feature: hospital-management-system, Property {number}: {property_text}**