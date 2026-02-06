#!/bin/bash

# Login and get token
echo "🔐 Logging in as admin..."
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

if [ -z "$TOKEN" ]; then
  echo "❌ Failed to login"
  exit 1
fi

echo "✅ Logged in successfully"
echo ""

# Add Dr. Nitish Tiwari (Orthopedic)
echo "👨‍⚕️  Adding Dr. Nitish Tiwari (Orthopedic)..."
curl -s -X POST "http://localhost:8000/api/v1/doctors/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dr. Nitish Tiwari",
    "department": "Orthopedic",
    "new_patient_fee": 500.00,
    "followup_fee": 300.00
  }' | python -m json.tool

echo ""

# Add Dr. Muskan Tiwari (Dentist)
echo "👩‍⚕️  Adding Dr. Muskan Tiwari (Dentist)..."
curl -s -X POST "http://localhost:8000/api/v1/doctors/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dr. Muskan Tiwari",
    "department": "Dentist",
    "new_patient_fee": 400.00,
    "followup_fee": 250.00
  }' | python -m json.tool

echo ""

# List all doctors
echo "📋 All Doctors in System:"
curl -s -X GET "http://localhost:8000/api/v1/doctors/" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
