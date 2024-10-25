import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
import os
load_dotenv()

# Gmail SMTP configuration
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")


def send_email(email):
    # Create email message
    Usermsg = EmailMessage()

    # Read HTML content from file with UTF-8 encoding
    with open("email.html", "r", encoding="utf-8") as file:
        html_content = file.read()

    Usermsg.set_content(html_content, subtype='html')  # Set content type to HTML
    Usermsg['Subject'] = "Your file is ready to download 🎉"
    Usermsg['From'] = EMAIL_ADDRESS
    Usermsg['To'] = email

    # Send email via SMTP
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(Usermsg)
        server.quit()
        print('Your message has been sent!', 'success')
    except Exception as e:
        print('There was an error sending your message. Please try again later.', 'danger')


send_email('sidhantraj0110@gmail.com')
