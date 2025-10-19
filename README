## DISCLAIMER

**USE AT YOUR OWN RISK. THE AUTHOR IS NOT RESPONSIBLE FOR ANY DAMAGES, DATA LOSS, OR OTHER ISSUES THAT MAY ARISE FROM THE USE OF THIS SOFTWARE. THIS APPLICATION IS PROVIDED AS-IS WITHOUT ANY WARRANTIES OR GUARANTEES.**

## Overview

Vehicle Management System is a self-hosted web application designed to help you track and manage all aspects of your vehicle maintenance, expenses, and records. Built with Python Flask and SQLite, this application runs entirely on your own infrastructure, ensuring complete data privacy and control.

## Screenshots

### Dashboard Overview
![Dashboard](screenshots/dashboard.png)

### Service Records Management
![Service Records](screenshots/service-records.png)

### Fuel Tracking
![Fuel Tracking](screenshots/fuel-tracking.png)

### Maintenance Reminders
![Reminders](screenshots/reminders.png)

## Features

### Vehicle Management
- Track multiple vehicles in your garage
- Store detailed vehicle information including make, model, year, and VIN
- Upload and manage vehicle photos
- Quick vehicle switching interface

### Service Records
- Comprehensive service history tracking
- Categorized maintenance records (Maintenance, Repair, Inspection, Upgrade)
- Odometer tracking for each service
- Cost tracking with currency support
- Document attachment support (PDF, images, Office documents)
- Full CRUD operations (Create, Read, Update, Delete)

### Fuel Economy Tracking
- Record fuel purchases and consumption
- Automatic fuel economy calculations (MPG/L per 100km)
- Cost analysis and trends
- Support for multiple fuel units (Gallons, Liters)
- Visual charts and statistics

### Recurring Expenses
- Track periodic costs (insurance, registration, taxes)
- Automated recurring expense management
- Frequency options: monthly, quarterly, yearly
- Next due date calculations

### Maintenance Reminders
- Schedule upcoming maintenance tasks
- Priority-based reminders (Low, Medium, High, Critical)
- Date-based and odometer-based reminders
- Notes and detailed descriptions

### Notes and Documentation
- Free-form notes for each vehicle
- Attach documents and images
- Organize vehicle-related information

### Data Management
- Export all data to CSV format
- Multi-language support (English, Romanian)
- Dark/Light theme toggle
- Responsive design for mobile and desktop

## Technical Stack

### Backend
- Python 3.9+
- Flask web framework
- SQLAlchemy ORM
- SQLite database
- Flask-Login for authentication
- Werkzeug for security

### Frontend
- Vanilla JavaScript
- CSS3 with modern features
- Responsive design
- Modal-based UI components
- Chart.js for data visualization

### Deployment
- Docker and Docker Compose
- Nginx reverse proxy support
- Volume-based persistent storage

## Installation

### Prerequisites

- Docker and Docker Compose installed
- Git installed
- Minimum 1GB RAM
- 5GB free disk space

### Quick Start

1. Clone the repository

git clone https://github.com/aiulian25/vehicle-management.git
cd vehicle-managemen

Build and start the application:

Access the application:
http://localhost:5000
Create your first account on the registration page.

### Manual Installation (Without Docker)

Clone the repository:
git clone https://github.com/aiulian25/vehicle-management.git


## Usage

### Adding a Vehicle

1. Click "Add Vehicle" button on the dashboard
2. Fill in vehicle details (make, model, year, VIN)
3. Optionally upload a vehicle photo
4. Save the vehicle

### Recording Service

1. Navigate to Service Records tab
2. Click "Add Service Record"
3. Enter date, odometer reading, description, and cost
4. Select category and add notes
5. Optionally attach documents
6. Save the record

### Tracking Fuel

1. Navigate to Fuel tab
2. Click "Add Fuel Record"
3. Enter date, odometer, fuel amount, and cost
4. View automatic MPG/consumption calculations
5. Analyze trends with charts

### Setting Reminders

1. Navigate to Reminders tab
2. Click "Add Reminder"
3. Enter description and select urgency
4. Set due date or odometer threshold
5. Add notes for the maintenance task

### Editing Records

1. Click the "Edit" button on any record
2. Modify the information in the modal
3. Save changes
4. Modal closes automatically after saving

### Deleting Records

1. Click the "Delete" button on any record
2. Confirm the deletion
3. Record is permanently removed

## Data Privacy and Security

- All data is stored locally on your server
- No external API calls or data transmission
- Password hashing using industry-standard algorithms
- Session-based authentication
- CSRF protection on all forms

## Backup and Restore

### Backup

The database file is located at `backend/vehicles.db`. To backup:


## Multi-Language Support

Supported languages:
- English
- Romanian

To add a new language:
1. Edit `frontend/static/js/translations.js`
2. Add translations for each key
3. Update the language selector in settings


The application will run with debug mode enabled and auto-reload on code changes.

### Adding New Features

1. Create a new branch
2. Implement the feature
3. Test thoroughly
4. Submit a pull request

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License

MIT License

Copyright (c) 2025 Vehicle Management System

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Acknowledgments

- Flask framework and its community
- Docker for containerization
- All contributors and users

## Support

For issues, questions, or feature requests, please open an issue on GitHub.

## Roadmap

- Mobile native applications
- API for third-party integrations
- Cloud sync option
- Multi-user support with role-based access
- Advanced reporting and analytics
- Integration with OBD-II devices

