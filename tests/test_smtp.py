import smtplib
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

def test_smtp_connection():
    print(f"Testing SMTP connection for: {SMTP_USER}")
    print(f"Connecting to {SMTP_SERVER}:{SMTP_PORT}...")
    
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=15)
        server.starttls()
        print("TLS started.")
        
        server.login(SMTP_USER, SMTP_PASSWORD)
        print("Login SUCCESS!")
        
        server.quit()
        print("Connection closed. SMTP test passed.")
        return True
    except smtplib.SMTPAuthenticationError:
        print("❌ SMTP AUTH ERROR: Check your email and app password.")
    except Exception as e:
        print(f"❌ SMTP FAILED: {e}")
    return False

if __name__ == "__main__":
    test_smtp_connection()
