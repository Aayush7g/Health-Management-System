# Health Management System

A Flask-based web application for managing appointments and medical records. This system allows patients to book appointments and view their medical history, while doctors can manage appointments and update patient records.

---

## Features

- **Patient Login**: Patients can book appointments and view their medical records.
- **Doctor Login**: Doctors can manage appointments and update patient records.
- **Nearby Hospitals Locator**: Patients can find nearby hospitals using an interactive map.
- **Medical Records Management**: Doctors can add and update medical records for patients.

---

## Technologies Used

- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS, Bootstrap
- **Database**: MySQL
- **APIs**: Twitter OAuth for authentication, Overpass API for hospital data
- **Mapping**: Leaflet.js for interactive maps

---

## Installation

Follow these steps to set up the project locally.

### Prerequisites

- Python 3.x
- MySQL
- Git

### Steps

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/health-management-system.git
   cd health-management-system


Set Up a Virtual Environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Set Up the Database:
Create a MySQL database named health_management.
Update the database configuration in the .env file:

```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=health_management
```

Usage
For Patients
Login: Use the "Patient Login" button to log in with Twitter.
Book Appointments: Select a doctor and choose an appointment date.
View Medical Records: Access your medical history from the dashboard.
Find Nearby Hospitals: Use the interactive map to locate nearby hospitals.

For Doctors
Login: Use the "Doctor Login" button to log in with Twitter.
Manage Appointments: View and manage your appointments.
Update Medical Records: Add or update medical records for your patients.
