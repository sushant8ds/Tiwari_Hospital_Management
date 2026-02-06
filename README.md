# Hospital OPD-IPD Management System

A comprehensive web-based hospital management system designed for real hospital operations in India. The system provides end-to-end management of outpatient (OPD) and inpatient (IPD) services, billing, investigations, procedures, operation theater management, employee management, and salary processing.

## Features

### Core Functionality
- **Patient Registration & Management**: Complete patient lifecycle management
- **OPD Management**: New patient registration and follow-up visits
- **IPD Management**: Inpatient admissions, bed allocation, and discharge
- **Billing System**: Comprehensive billing for all services and procedures
- **Investigation Management**: X-Ray, ECG, Blood tests, and custom investigations
- **Procedure & Services**: Medical procedures and hospital services billing
- **Operation Theater**: OT charges and surgical procedure management
- **Employee Management**: Staff records and salary processing

### Key Features
- **Barcode Integration**: All slips include barcodes for quick patient identification
- **Role-Based Access Control**: Separate access levels for Reception and Admin users
- **Print-Ready Slips**: Support for both A4 and thermal printer formats
- **Real-Time Dashboard**: Live statistics and quick action buttons
- **Comprehensive Reporting**: Daily reports, revenue analysis, and occupancy statistics
- **Data Backup & Recovery**: Automated backup and data export capabilities
- **Audit Trail**: Complete logging of all manual charges and modifications

## Technology Stack

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Frontend**: Bootstrap 5 with vanilla JavaScript
- **Authentication**: JWT-based authentication
- **Migrations**: Alembic for database schema management
- **Barcode**: Python-barcode and QRCode libraries
- **PDF Generation**: ReportLab for slip generation

## Installation

### Prerequisites
- Python 3.8 or higher
- PostgreSQL 12 or higher
- pip (Python package manager)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd hospital-management-system
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env file with your database credentials and configuration
   ```

5. **Setup database**
   ```bash
   # Create database
   createdb hospital_db
   
   # Run migrations
   alembic upgrade head
   ```

6. **Run the application**
   ```bash
   python run.py
   ```

The application will be available at `http://localhost:8000`

## Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/hospital_db

# Application Configuration
SECRET_KEY=your-secret-key-here
HOSPITAL_NAME=Your Hospital Name
HOSPITAL_ADDRESS=Your Hospital Address
HOSPITAL_PHONE=+91-XXXXXXXXXX

# Environment
ENVIRONMENT=development
```

### Database Setup

1. **Create PostgreSQL database**
   ```sql
   CREATE DATABASE hospital_db;
   CREATE USER hospital_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE hospital_db TO hospital_user;
   ```

2. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

## Usage

### Default Access

The system supports two user roles:

- **Admin User**: Full system access including manual charges, doctor management, reports
- **Reception User**: Patient registration, billing, investigations, procedures, services

### Key Workflows

1. **Patient Registration**
   - Register new patients with mandatory fields
   - Generate unique Patient ID automatically
   - Print OPD slip with barcode

2. **OPD Management**
   - New patient registration with doctor selection
   - Follow-up visits with daily serial numbers
   - Automatic fee calculation based on visit type

3. **IPD Management**
   - Convert OPD patients to IPD
   - Bed allocation with ward type selection
   - Discharge with comprehensive billing

4. **Billing & Charges**
   - Add investigation charges
   - Record procedures and services
   - Manual charge entry for custom services
   - Generate final discharge bills

## API Documentation

Once the server is running, visit `http://localhost:8000/docs` for interactive API documentation.

### Key Endpoints

- `POST /api/v1/patients/` - Register new patient
- `POST /api/v1/visits/opd` - Create OPD visit
- `POST /api/v1/ipd/admit` - Admit patient to IPD
- `POST /api/v1/billing/{visit_id}/investigations` - Add investigation charges
- `GET /api/v1/reports/daily` - Generate daily reports

## Testing

Run the test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=app tests/
```

## Development

### Project Structure

```
hospital-management-system/
├── app/
│   ├── api/                 # API endpoints
│   ├── core/                # Core configuration
│   ├── models/              # Database models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   └── utils/               # Utilities
├── alembic/                 # Database migrations
├── static/                  # Static files (CSS, JS, images)
├── templates/               # HTML templates
├── tests/                   # Test files
└── requirements.txt         # Python dependencies
```

### Adding New Features

1. Create database models in `app/models/`
2. Add Pydantic schemas in `app/schemas/`
3. Implement business logic in `app/services/`
4. Create API endpoints in `app/api/v1/endpoints/`
5. Add tests in `tests/`

### Database Migrations

Create new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

## Deployment

### Production Setup

1. **Environment Configuration**
   ```env
   ENVIRONMENT=production
   DATABASE_URL=postgresql://user:pass@localhost:5432/hospital_prod
   SECRET_KEY=strong-production-secret-key
   ```

2. **Database Setup**
   ```bash
   alembic upgrade head
   ```

3. **Run with Gunicorn**
   ```bash
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

### Docker Deployment

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation at `/docs`

## Changelog

### Version 1.0.0
- Initial release
- Complete OPD/IPD management
- Billing and charging system
- Barcode integration
- Role-based access control
- Comprehensive reporting