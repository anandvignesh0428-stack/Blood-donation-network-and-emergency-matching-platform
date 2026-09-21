# Blood Donation Network and Emergency Matching Platform

A platform to connect blood donors with patients during emergency situations.

## Features

- **Donor Registration**: Register blood donors with name, blood group, location, phone, and availability
- **Emergency Blood Requests**: Create emergency requests with patient details, blood group, location, hospital, and contact
- **Smart Matching**: Find compatible donors based on blood group compatibility and location
- **Blood Compatibility**: Standard red blood cell compatibility (A+, A-, B+, B-, AB+, AB-, O+, O-)
- **Voice Input**: Voice-to-text for emergency request fields (microphone required)
- **Dashboard**: Statistics on donors and requests
- **Request Status Management**: Track requests from Pending → Matched → Completed

## Setup

### Prerequisites

- Python 3.10+
- pip

### Installation

1. Create and activate a virtual environment:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) For voice recognition, install system dependencies:
   - Windows: No additional steps needed
   - Linux: `sudo apt-get install python3-pyaudio portaudio19-dev`
   - Mac: `brew install portaudio`

## Running the Application

```bash
# From the project directory
uvicorn main:app --reload
```

The application will be available at:
- **Home**: http://localhost:8000/
- **Donor Registration**: http://localhost:8000/donor
- **Emergency Requests**: http://localhost:8000/emergency
- **Find Matching Donors**: http://localhost:8000/matching
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/donors` | Register a new donor |
| GET | `/donors` | List all donors |
| PUT | `/donors/{id}/availability` | Toggle donor availability |
| POST | `/emergency-requests` | Create emergency request |
| GET | `/emergency-requests` | List all emergency requests |
| GET | `/match/{request_id}` | Find matching donors for a request |
| PUT | `/emergency-requests/{id}/status` | Update request status |
| GET | `/dashboard` | Get statistics |
| POST | `/voice/recognize` | Voice recognition (microphone required) |

## Blood Group Compatibility

| Patient Blood Group | Can Receive From |
|---------------------|------------------|
| A+ | A+, A-, O+, O- |
| A- | A-, O- |
| B+ | B+, B-, O+, O- |
| B- | B-, O- |
| AB+ | All types |
| AB- | A-, B-, AB-, O- |
| O+ | O+, O- |
| O- | O- |

## Project Structure

```
Blood_Donation_Network/
├── main.py              # FastAPI application
├── models.py            # SQLAlchemy models
├── schemas.py           # Pydantic validation schemas
├── database.py          # Database configuration
├── requirements.txt     # Python dependencies
├── templates/
│   ├── index.html       # Home page
│   ├── donor.html       # Donor registration page
│   ├── emergency.html   # Emergency request page (with voice input)
│   └── matching.html    # Donor matching page
├── blood_donation.db    # SQLite database (auto-created)
└── voice_test.py        # Standalone voice test script
```

## Usage

1. **Register Donors**: Go to `/donor` and add donors with their blood group and location
2. **Create Emergency Request**: Go to `/emergency` and submit a request (use 🎤 buttons for voice input)
3. **Find Matches**: Go to `/matching` to see all requests and click "Find Matching Donors"
4. **Track Status**: Update request status from the emergency page

## Notes

- Voice recognition requires a working microphone and internet connection (uses Google Speech Recognition)
- The application uses SQLite for simplicity; for production, consider PostgreSQL
- Blood groups are automatically normalized to uppercase (e.g., "b+" → "B+")
- Input validation ensures data quality on both frontend and backend