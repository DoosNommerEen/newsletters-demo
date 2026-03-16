"""Gmail email sending tool using SMTP with STARTTLS.

Builds a styled HTML newsletter email and sends it via Gmail using an App Password.
Recipients are read from the NEWSLETTER_RECIPIENTS environment variable.
"""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

log = logging.getLogger(__name__)

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def _build_html(summary: dict, gamma_url: str, week_label: str) -> str:
    """Build the HTML email body."""
    top_trends_html = "".join(
        f"<li style='margin-bottom:8px;'>{t}</li>"
        for t in summary.get("top_trends", [])
    )

    key_insights_html = "".join(
        f"<p style='margin:0 0 12px 0;'>{insight}</p>"
        for insight in summary.get("key_insights", [])
    )

    developments_html = "".join(
        f"""
        <div style='background:#f8f9fa;border-left:4px solid #4f46e5;padding:12px 16px;
                    margin-bottom:12px;border-radius:0 4px 4px 0;'>
          <strong style='color:#1e1b4b;'>{d.get('title', '')}</strong><br>
          <span style='color:#374151;font-size:14px;'>{d.get('summary', '')}</span><br>
          <a href='{d.get('url', '#')}' style='color:#4f46e5;font-size:13px;text-decoration:none;'>
            Read more →
          </a>
        </div>
        """
        for d in summary.get("notable_developments", [])
    )

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI & Tech Trends — {week_label}</title>
</head>
<body style="margin:0;padding:0;background-color:#f3f4f6;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f3f4f6;padding:32px 16px;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0"
               style="max-width:600px;width:100%;background:#ffffff;border-radius:8px;
                      overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">

          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#4f46e5 0%,#7c3aed 100%);
                       padding:32px 40px;text-align:center;">
              <p style="margin:0 0 4px 0;color:rgba(255,255,255,0.8);font-size:13px;
                        letter-spacing:2px;text-transform:uppercase;">Weekly Briefing</p>
              <h1 style="margin:0;color:#ffffff;font-size:26px;font-weight:700;
                         line-height:1.2;">AI &amp; Tech Trends</h1>
              <p style="margin:8px 0 0 0;color:rgba(255,255,255,0.85);font-size:14px;">
                {week_label}
              </p>
            </td>
          </tr>

          <!-- Intro -->
          <tr>
            <td style="padding:32px 40px 0 40px;">
              <p style="margin:0;color:#374151;font-size:16px;line-height:1.6;">
                {summary.get('newsletter_intro', '')}
              </p>
            </td>
          </tr>

          <!-- Gamma CTA -->
          <tr>
            <td style="padding:24px 40px;">
              <table width="100%" cellpadding="0" cellspacing="0"
                     style="background:#eef2ff;border-radius:8px;padding:0;">
                <tr>
                  <td style="padding:20px 24px;">
                    <p style="margin:0 0 4px 0;color:#4f46e5;font-size:12px;
                               font-weight:700;letter-spacing:1px;text-transform:uppercase;">
                      This Week's Presentation
                    </p>
                    <p style="margin:0 0 16px 0;color:#1e1b4b;font-size:15px;font-weight:600;">
                      View the full AI &amp; Tech Trends slide deck on Gamma
                    </p>
                    <a href="{gamma_url}"
                       style="display:inline-block;background:#4f46e5;color:#ffffff;
                              text-decoration:none;padding:10px 24px;border-radius:6px;
                              font-size:14px;font-weight:600;">
                      View Full Presentation →
                    </a>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Top Trends -->
          <tr>
            <td style="padding:0 40px 24px 40px;">
              <h2 style="margin:0 0 16px 0;color:#1e1b4b;font-size:18px;font-weight:700;
                         border-bottom:2px solid #e5e7eb;padding-bottom:8px;">
                Top Trends This Week
              </h2>
              <ol style="margin:0;padding-left:20px;color:#374151;font-size:15px;line-height:1.6;">
                {top_trends_html}
              </ol>
            </td>
          </tr>

          <!-- Key Insights -->
          <tr>
            <td style="padding:0 40px 24px 40px;">
              <h2 style="margin:0 0 16px 0;color:#1e1b4b;font-size:18px;font-weight:700;
                         border-bottom:2px solid #e5e7eb;padding-bottom:8px;">
                Key Insights
              </h2>
              <div style="color:#374151;font-size:15px;line-height:1.7;">
                {key_insights_html}
              </div>
            </td>
          </tr>

          <!-- Notable Developments -->
          <tr>
            <td style="padding:0 40px 32px 40px;">
              <h2 style="margin:0 0 16px 0;color:#1e1b4b;font-size:18px;font-weight:700;
                         border-bottom:2px solid #e5e7eb;padding-bottom:8px;">
                Notable Developments
              </h2>
              {developments_html}
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background:#f9fafb;border-top:1px solid #e5e7eb;
                       padding:20px 40px;text-align:center;">
              <p style="margin:0;color:#9ca3af;font-size:12px;line-height:1.6;">
                This newsletter is generated automatically each Monday using AI-powered research.<br>
                Sources are linked inline above.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def run_send_email(summary: dict, gamma_url: str, week_label: str) -> None:
    """Build and send the HTML newsletter email via Gmail SMTP.

    Args:
        summary: Structured summary dict from summarise.run_summarise.
        gamma_url: Public Gamma presentation URL from create_presentation.run_create_presentation.
        week_label: Human-readable week label (e.g. "Week of March 14, 2026").

    Raises:
        RuntimeError: If required environment variables are missing.
        smtplib.SMTPException: On SMTP delivery errors.
    """
    sender = os.environ.get("GMAIL_SENDER")
    app_password = os.environ.get("GMAIL_APP_PASSWORD")
    recipients_raw = os.environ.get("NEWSLETTER_RECIPIENTS", "")

    if not sender:
        raise RuntimeError("GMAIL_SENDER environment variable is not set.")
    if not app_password:
        raise RuntimeError("GMAIL_APP_PASSWORD environment variable is not set.")
    if not recipients_raw:
        raise RuntimeError("NEWSLETTER_RECIPIENTS environment variable is not set.")

    recipients = [r.strip() for r in recipients_raw.split(",") if r.strip()]
    subject = f"AI & Tech Trends — {week_label}"
    html_body = _build_html(summary, gamma_url, week_label)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(html_body, "html"))

    log.info("Connecting to Gmail SMTP (%s:%d)...", SMTP_HOST, SMTP_PORT)
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(sender, app_password)
        smtp.sendmail(sender, recipients, msg.as_string())

    log.info("Email sent successfully to: %s", ", ".join(recipients))
