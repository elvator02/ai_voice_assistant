
# AI Appointment System

This project provides an API for checking appointment availability and sending confirmation emails. It uses FastAPI for the backend, Google Sheets API for storing appointments, and an email service for sending confirmations. Below is an overview of how to set up and use this system.

## Features
1. **Check Appointment Availability**: The `/checkappointmenttime` endpoint checks if a requested time slot is available.
2. **Make Appointment**: The `/makeappoint` endpoint schedules an appointment, sends an email confirmation, and records the appointment in a Google Sheet.
3. **Logging**: Logs API requests to a Google Sheet for monitoring purposes.
4. **Email Confirmation**: Automatically sends an email confirmation for booked appointments.
   
## Dependencies
- FastAPI
- Uvicorn
- Google Sheets API (via `gspread`)
- SMTP (for email functionality)

## Setup Instructions

1. **Install Required Libraries**
   Make sure you have all dependencies installed by running:
   ```bash
   pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib gspread fastapi uvicorn smtplib
   ```

2. **Google Sheets API Credentials**
   To use the Google Sheets API, you’ll need to set up Google API credentials:
   
   1. Go to the [Google Developers Console](https://console.developers.google.com/).
   2. Create a new project.
   3. Enable the Google Sheets API.
   4. Create service account credentials and download the JSON file.
   5. Share your Google Sheet with the service account email (found in the credentials JSON).

   For more information on how to set up credentials for the Google Sheets API, refer to the following video:
   
   [How to Get Google Sheets API Credentials](https://www.youtube.com/watch?v=zCEJurLGFRk&t=893s&pp=ygUQZ29vZ2xlIHNoZWV0IGFwaQ%3D%3D)

3. **Update Configuration**
   - Replace `creds.json` with your credentials file.
   - Set the `GOOGLE_SHEET_ID` and the `GOOGLE_APP_MAIL` (for email) in the `secret_keys.py` file.

4. **Run the Server**
   Once everything is set up, you can run the server with:
   ```bash
   python server.py
   ```

   This will start the FastAPI server locally at `http://127.0.0.1:5000`.

## Endpoints

### `/checkappointmenttime`
- **Method**: `POST`
- **Description**: Checks if the requested time slot is available based on the existing appointments in the Google Sheet.
- **Request Body**: Contains the requested appointment time window.
- **Response**: A message indicating whether the time slot is available or not.

### `/makeappoint`
- **Method**: `POST`
- **Description**: Schedules an appointment, sends an email, and logs it to Google Sheets.
- **Request Body**: Contains the email, name, date, and intent for the appointment.
- **Response**: Confirmation message indicating whether the appointment was successfully scheduled.

### `/logs`
- **Method**: `POST`
- **Description**: Logs API request data to a Google Sheet for monitoring purposes.
- **Request Body**: Raw request data.
- **Response**: Logs the request to the sheet.

## Demo

To get a better idea of how the appointment system works, you can watch the following video demonstrating the workflow of this project:

[Appointment System Demo](https://www.youtube.com/watch?v=NA5Rxovk2Hg)

## Further Improvements

1. To Cancel Appointments
2. To Use More Persistance Database

---
