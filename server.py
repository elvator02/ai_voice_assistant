from fastapi import FastAPI
from fastapi.requests import Request
import uvicorn
from email.message import EmailMessage
import smtplib
import gspread
from google.oauth2.service_account import Credentials
import logging
from datetime import datetime, timedelta
import json
import secret_keys as keys

# Configure logging similar to Uvicorn
logging.basicConfig(
    format="%(levelname)s:     %(asctime)s - %(client_ip)s - \"%(method)s %(path)s %(status_code)s\"",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Google Sheets Configuration
scopes = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file('creds.json', scopes=scopes)
client = gspread.authorize(creds)
sheet_id = keys.GOOGLE_SHEET_ID
sheet = client.open_by_key(sheet_id).sheet1
appointment_sheet = client.open_by_key(sheet_id).worksheet('Sheet2')

app = FastAPI()


class Logger:
    def __init__(self, sheet):
        self.sheet = sheet

    def log_request(self, request: Request, data : dict, additionalmsg : str):
        client_host = request.client.host if request.client else "Unknown"
        user_agent = request.headers.get('User-Agent', 'Unknown')
        request_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")  # UTC timestamp
        method = request.method
        path = request.url.path
        status_code = 200

        log_message = f"INFO:     {client_host} - \"{method} {path} {status_code}\""
        logging.info(log_message, extra={"client_ip": client_host, "method": method, "path": path, "status_code": status_code})
        print(data["message"]["call"]["id"])
        additionalmsg = additionalmsg if additionalmsg else ""

        log_entry = [
            request_time,  
            client_host,
            method,
            path,
            status_code,
            user_agent,
            data["message"]["call"]["id"],
            additionalmsg,
            json.dumps(data) if data else "No data" 
        ]

        headers = ["Timestamp", "IP Address", "Method", "Path", "Status Code", "User-Agent", "Call Id", "Additional Msg", "Data"]

        if not self.sheet.get_all_records():  
            self.sheet.append_row(headers)
        self.sheet.append_row(log_entry)


logger = Logger(sheet)


def send_email(email: str, name: str, date: str, intent: str) -> bool:
    success = False
    date_obj = datetime.fromisoformat(date)

    formatted_date = date_obj.strftime("%B %d, %Y at %I:%M %p")

    message = f"""
    <html>
    <body>
        <h2>Appointment Confirmation</h2>
        <p>Dear {name},</p>
        <p>This is to confirm that you have successfully booked an appointment with Mr. Kushagra.</p>

        <p><strong>Appointment Details:</strong></p>
        <ul>
            <li><strong>Date and Time:</strong> {formatted_date}</li>
            <li><strong>Location:</strong> Mr. Kushagra's Office</li>
            <li><strong>Contact Number:</strong> 123456789</li>
            <li><strong>Purpose of Appointment:</strong> {intent}</li>
        </ul>

        <p>If you have any questions or need to reschedule, feel free to reach out to Mr. Kushagra at <strong>123456789</strong>.</p>

        <p>Thank you for scheduling with us!</p>
        <br>
        <p>Best regards,</p>
        <p><strong>Mr. Kushagra</strong><br>Appointment Coordinator</p>
    </body>
    </html>
    """

    try:
        em = EmailMessage()
        em['Subject'] = "Appointment Confirmation"
        em['From'] = keys.GOOGLE_APP_MAIL
        em['To'] = email

        em.set_content(message, subtype='html')

        # Send the email via Gmail's SMTP server
        s = smtplib.SMTP('smtp.gmail.com', 587)
        s.starttls()
        s.login(keys.GOOGLE_APP_MAIL, keys.GOOGLE_APP_KEY)
        s.sendmail(keys.GOOGLE_APP_MAIL, email, em.as_string())
        s.quit()

        success = True
    except Exception as e:
        print(f"An error occurred: {e}")

    return success

@app.post("/checkappointmenttime")
async def check_appointment_time(request: Request):
    data = await request.json()
    tool_call = data['message']['toolCalls']
    success = True

    for call in tool_call:
        if call['function']['name'] == 'checkAppointmentTime':
            requested_from = call['function']['arguments']['from']
            requested_to = call['function']['arguments']['to']
            print(requested_from, " endtime ",requested_to)

            # Convert input times to datetime objects
            from_time = datetime.fromisoformat(requested_from)
            to_time = datetime.fromisoformat(requested_to)
            appointment_time_from = from_time
            appointment_time_to = to_time

            existing_appointments = appointment_sheet.get_all_records()

            for appointment in existing_appointments:
                existing_from = datetime.fromisoformat(appointment['From'])
                existing_to = datetime.fromisoformat(appointment['To'])

                # Check for overlap: (new start < existing end) and (new end > existing start)
                if appointment_time_from < existing_to and appointment_time_to > existing_from:
                    success = False
                    break

            tool_id = call['id']
            break

    success_msg = "Appointment time slot is available" if success else "No available time slot"
    print(success_msg)
    logger.log_request(request, data, success_msg)

    return {
        'results': [
            {
                'toolCallId': tool_id,
                'result': success_msg
            }
        ]
    }


def write_appointment_to_sheet(requested_from: str, requested_to: str, name: str, email: str, intent: str, appointment_sheet) -> bool:
    try:

        appointment_from = datetime.fromisoformat(requested_from).isoformat()
        appointment_to = datetime.fromisoformat(requested_to).isoformat()

        appointment_data = [
            appointment_from,  # From Time (ISO format)
            appointment_to,    # To Time (ISO format)
            name,              # Name of the person
            email,             # Email address
            intent,            # Purpose of the appointment
        ]

        headers = ["From", "To", "Name", "Email", "Intent"]

        if not appointment_sheet.get_all_records():  
            appointment_sheet.append_row(headers)

        appointment_sheet.append_row(appointment_data)
        print("Appointment successfully scheduled!")
        return True
    except Exception as e:
        print(f"Error while writing appointment to sheet: {e}")
        return False    

@app.post("/makeappoint")
async def mmakeappointment(request: Request):
    data = await request.json()
    tool_call = data['message']['toolCalls']
    success = False
    for call in tool_call:
        if call['function']['name'] == 'makeAppointment':
            email = call['function']['arguments']['email']
            name = call['function']['arguments']['name']
            date = call['function']['arguments']['date']
            intent = call['function']['arguments']['intent']
            from_time = datetime.fromisoformat(date)
            to_time = from_time + timedelta(minutes=30)
            from_time = from_time.isoformat()
            to_time = to_time.isoformat()
            success = send_email(email, name, date, intent)
            if success:
                success = write_appointment_to_sheet(from_time, to_time, name, email, intent, appointment_sheet)
            tool_id = call['id']
            break

    success_msg = "Email sent successfully!" if success else "Failed to send email."

    logger.log_request(request, data, success_msg)
    return {
        'results': [
            {
                'toolCallId': tool_id,
                'result': success_msg
            }
        ]
    }


@app.post("/logs")
async def log_api(request: Request):
    data = await request.json() 
    additional_msg = ""
    logger.log_request(request, data, additional_msg)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
