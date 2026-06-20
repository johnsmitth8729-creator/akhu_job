import smtplib
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.models import db, SystemSetting, Notification

def send_email_notification(recipient, subject, body):
    # Fetch SMTP details from database settings
    smtp_host = SystemSetting.get_setting('email_smtp_host', 'localhost')
    smtp_port_str = SystemSetting.get_setting('email_smtp_port', '587')
    smtp_user = SystemSetting.get_setting('email_smtp_user', '')
    smtp_password = SystemSetting.get_setting('email_smtp_password', '')
    from_address = SystemSetting.get_setting('email_from_address', 'no-reply@akhu.edu.uz')
    use_tls_str = SystemSetting.get_setting('email_use_tls', 'True')
    
    # Save log entry
    notif = Notification(
        type='email',
        recipient=recipient,
        subject=subject,
        message=body,
        is_sent=False
    )
    db.session.add(notif)
    db.session.commit()
    
    # Simple check for valid Port
    try:
        smtp_port = int(smtp_port_str)
    except ValueError:
        smtp_port = 587
        
    use_tls = use_tls_str.lower() in ('true', '1', 'yes')
    
    print(f"Sending email notification to {recipient}...")
    
    # Construct email message
    msg = MIMEMultipart()
    msg['From'] = from_address
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    
    try:
        # Check if local/testing stub or default setting
        if smtp_host in ('localhost', '127.0.0.1') and not smtp_user:
            # For development, just output to console and flag as sent
            notif.is_sent = True
            notif.sent_at = datetime.datetime.utcnow()
            db.session.commit()
            print("=========================================")
            print(f"DEVELOPMENT EMAIL OUTBOX (Sent via local stub):")
            print(f"To: {recipient}")
            print(f"Subject: {subject}")
            print(f"Body: {body}")
            print("=========================================")
            return True
            
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
        if use_tls:
            server.starttls()
            
        if smtp_user and smtp_password:
            server.login(smtp_user, smtp_password)
            
        server.sendmail(from_address, recipient, msg.as_string())
        server.quit()
        
        notif.is_sent = True
        notif.sent_at = datetime.datetime.utcnow()
        db.session.commit()
        return True
        
    except Exception as e:
        notif.error_message = str(e)
        db.session.commit()
        print(f"Email notification error: {e}")
        return False
