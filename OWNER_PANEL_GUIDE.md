# Owner/Admin Panel Guide

## Overview
A comprehensive Owner/Admin panel has been added to the Hospital Management System with employee and salary management features.

## Features Added

### 1. Owner Dashboard (`/owner`)
- Quick stats showing:
  - Total Doctors
  - Total Employees
  - Pending Salary Payments
  - Monthly Payroll
- Quick access cards to:
  - Doctor Management
  - Employee Management
  - Salary Management

### 2. Doctor Management (`/owner/doctors`)
- View all doctors with their details
- Add new doctors
- Edit existing doctor information:
  - Name
  - Department
  - New Patient Fee
  - Follow-up Fee
  - Status (Active/Inactive)

### 3. Employee Management (`/owner/employees`)
- View all employees with complete details:
  - Employee ID
  - Name
  - Post
  - Qualifications
  - Employment Status (Permanent/Probation)
  - Duty Hours
  - Joining Date
  - Monthly Salary
  - Status (Active/Inactive)
- Add new employees
- Edit employee details including salary changes

### 4. Salary Management (`/owner/salaries`)
- Track all salary payments
- Filter by:
  - Month
  - Year
  - Status (Pending/Paid)
- Mark pending payments as paid
- View payment history
- Add notes to payments

## Access Control

### Role-Based Access
- **Owner menu is ONLY visible to ADMIN users**
- All owner endpoints require ADMIN role authentication
- Regular users (RECEPTION role) cannot access owner features

### How to Access
1. Login with an ADMIN account
2. The "Owner" menu item will appear in the left sidebar
3. Click "Owner" to access the dashboard

## Database Models

### SalaryPayment Model
New table: `salary_payments`
- `payment_id`: Unique payment identifier
- `employee_id`: Foreign key to employees table
- `month`: Payment month (1-12)
- `year`: Payment year
- `amount`: Salary amount
- `payment_date`: Date when salary was paid (null if pending)
- `status`: PENDING or PAID
- `notes`: Optional payment notes

## API Endpoints

### Doctor Management
- `POST /api/v1/owner/doctors` - Create doctor
- `PUT /api/v1/owner/doctors/{doctor_id}` - Update doctor

### Employee Management
- `POST /api/v1/owner/employees` - Create employee
- `GET /api/v1/owner/employees` - Get all employees
- `GET /api/v1/owner/employees/{employee_id}` - Get employee by ID
- `PUT /api/v1/owner/employees/{employee_id}` - Update employee

### Salary Management
- `POST /api/v1/owner/salary-payments` - Create salary payment record
- `GET /api/v1/owner/salary-payments` - Get all payments (with filters)
- `GET /api/v1/owner/salary-payments/pending` - Get pending payments
- `POST /api/v1/owner/salary-payments/{payment_id}/mark-paid` - Mark as paid
- `PUT /api/v1/owner/salary-payments/{payment_id}` - Update payment

## UI Design

### Professional & Simple
- Clean card-based layout
- Color-coded status badges:
  - Green: Active/Paid/Permanent
  - Yellow: Pending/Probation
  - Gray: Inactive
- Responsive tables with hover effects
- Modal dialogs for add/edit operations
- Toast notifications for user feedback

### Navigation
- Owner menu item in left sidebar (ADMIN only)
- Breadcrumb-style navigation
- Quick action buttons
- Filter controls for data views

## Usage Examples

### Adding an Employee
1. Go to `/owner/employees`
2. Click "Add Employee" button
3. Fill in the form:
   - Name, Post, Qualifications
   - Employment Status, Duty Hours
   - Joining Date, Monthly Salary
4. Click "Add Employee"

### Managing Salaries
1. Go to `/owner/salaries`
2. Filter by month/year to see specific period
3. View pending payments
4. Click "Mark Paid" on pending payments
5. Enter payment date and optional notes
6. Confirm to mark as paid

### Updating Doctor Fees
1. Go to `/owner/doctors`
2. Click edit icon on doctor row
3. Update fees or other details
4. Click "Update Doctor"

## Security Notes

- All owner endpoints require authentication
- Only ADMIN role can access owner features
- JWT token validation on every request
- Role checking at both frontend and backend

## Deployment

The changes have been pushed to GitHub and will be automatically deployed to Render. The database will automatically create the new `salary_payments` table on startup.

## Next Steps

To start using the owner panel:
1. Ensure you have an ADMIN user account
2. Login to the system
3. The "Owner" menu will appear in the sidebar
4. Start managing doctors, employees, and salaries!
