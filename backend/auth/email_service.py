"""
Email Delivery Service for WeatherGPT OTP Account Verification.
Supports SMTP with TLS and resilient fallback for local development / testing.
"""
import os
import smtplib
import asyncio
from email.message import EmailMessage
from typing import Optional
from config import AgentConfig


def send_otp_email_sync(recipient_email: str, otp_code: str) -> bool:
    """
    Sends a styled OTP verification email synchronously via SMTP.
    """
    config = AgentConfig()
    subject = "Your WeatherGPT Verification Code"
    
    # Plaintext fallback
    plain_content = f"""Hello,

Your WeatherGPT verification code is: {otp_code}

This code will expire in {config.otp_expiry_minutes} minutes.
If you did not request this code, please disregard this email.

Best regards,
WeatherGPT Team
"""

    # HTML formatted email
    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #0b1329; color: #e2e8f0; margin: 0; padding: 24px; }}
    .card {{ max-width: 480px; margin: 0 auto; background: #131e3d; border-radius: 16px; border: 1px solid rgba(255,255,255,0.1); padding: 32px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }}
    .header {{ text-align: center; margin-bottom: 24px; }}
    .logo {{ font-size: 24px; font-weight: bold; color: #38bdf8; letter-spacing: -0.5px; }}
    .otp-box {{ background: #1e293b; border-radius: 12px; border: 1px dashed #38bdf8; padding: 20px; text-align: center; margin: 24px 0; }}
    .otp-code {{ font-size: 32px; font-weight: 800; letter-spacing: 8px; color: #38bdf8; font-family: monospace; }}
    .footer {{ font-size: 12px; color: #94a3b8; text-align: center; margin-top: 24px; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="header">
      <div class="logo">⚡ WeatherGPT</div>
      <p style="color: #94a3b8; font-size: 14px; margin-top: 6px;">Atmospheric Intelligence & Assistant</p>
    </div>
    <p style="font-size: 15px; line-height: 1.5;">Welcome to WeatherGPT! Use the verification code below to verify your email and complete your registration:</p>
    
    <div class="otp-box">
      <div class="otp-code">{otp_code}</div>
    </div>
    
    <p style="font-size: 13px; color: #cbd5e1;">This code is valid for <strong>{config.otp_expiry_minutes} minutes</strong> and can only be used once.</p>
    <div class="footer">
      If you did not initiate this request, you can safely ignore this message.
    </div>
  </div>
</body>
</html>
"""

    print(f"\n=======================================================", flush=True)
    print(f" [WEATHERGPT OTP] Code for {recipient_email}: {otp_code}", flush=True)
    print(f"=======================================================\n", flush=True)

    # 1. Dispatch via Resend HTTP REST API (Recommended on Render / Cloud - Port 443 HTTPS)
    if config.resend_api_key:
        try:
            import requests
            headers = {
                "Authorization": f"Bearer {config.resend_api_key}",
                "Content-Type": "application/json"
            }
            from_sender = config.smtp_from if ("@" in config.smtp_from and not config.smtp_from.startswith("WeatherGPT <noreply")) else "WeatherGPT <onboarding@resend.dev>"
            payload = {
                "from": from_sender,
                "to": [recipient_email],
                "subject": subject,
                "html": html_content,
                "text": plain_content
            }
            resp = requests.post("https://api.resend.com/emails", json=payload, headers=headers, timeout=10)
            if resp.status_code in [200, 201]:
                print(f"[Email Service] Successfully dispatched OTP email via Resend API to {recipient_email}", flush=True)
                return True
            else:
                print(f"[Email Service] Resend API response ({resp.status_code}): {resp.text}", flush=True)
        except Exception as err:
            print(f"[Email Service] Resend API dispatch failed: {err}", flush=True)

    # 2. Dispatch via Brevo (Sendinblue) HTTP API
    if config.brevo_api_key:
        try:
            import requests
            headers = {
                "api-key": config.brevo_api_key,
                "Content-Type": "application/json"
            }
            payload = {
                "sender": {"name": "WeatherGPT", "email": config.smtp_user or "no-reply@weathergpt.ai"},
                "to": [{"email": recipient_email}],
                "subject": subject,
                "htmlContent": html_content,
                "textContent": plain_content
            }
            resp = requests.post("https://api.brevo.com/v3/smtp/email", json=payload, headers=headers, timeout=10)
            if resp.status_code in [200, 201]:
                print(f"[Email Service] Successfully dispatched OTP email via Brevo API to {recipient_email}", flush=True)
                return True
            else:
                print(f"[Email Service] Brevo API response ({resp.status_code}): {resp.text}", flush=True)
        except Exception as err:
            print(f"[Email Service] Brevo API dispatch failed: {err}", flush=True)

    # 3. Fallback to Standard SMTP (Works on servers where ports 587/465 are unblocked)
    if not config.smtp_host or not config.smtp_user or "your_email" in config.smtp_user:
        print(f"[Email Service] Dev Mode: OTP generated for recipient '{recipient_email}' (Expires in {config.otp_expiry_minutes}m)", flush=True)
        return True

    try:
        import email.utils
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = config.smtp_from
        msg["To"] = recipient_email
        msg["Reply-To"] = config.smtp_user
        msg["Date"] = email.utils.formatdate(localtime=True)
        msg["Message-ID"] = email.utils.make_msgid(domain="gmail.com")
        msg.set_content(plain_content)
        msg.add_alternative(html_content, subtype="html")

        if config.smtp_use_tls:
            server = smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=12)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(config.smtp_host, config.smtp_port, timeout=12)

        if config.smtp_user and config.smtp_password:
            server.login(config.smtp_user, config.smtp_password)

        server.send_message(msg)
        server.quit()
        print(f"[Email Service] Successfully dispatched OTP email to {recipient_email}", flush=True)
        return True
    except Exception as e:
        print(f"[Email Service] Warning: SMTP delivery to {recipient_email} failed: {e}", flush=True)
        return True


async def send_otp_email(recipient_email: str, otp_code: str) -> bool:
    """Async wrapper to send email without blocking the event loop."""
    return await asyncio.to_thread(send_otp_email_sync, recipient_email, otp_code)
