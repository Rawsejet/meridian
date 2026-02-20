"""Email service for sending notifications."""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

from app.core.config import get_settings


class EmailService:
    """Service for sending emails via SMTP."""

    def __init__(self):
        self.settings = get_settings()

    def _create_message(
        self, to_email: str, subject: str, body: str, is_html: bool = False
    ) -> MIMEMultipart:
        """Create an email message."""
        msg = MIMEMultipart()
        msg["From"] = self.settings.smtp_from_email
        msg["To"] = to_email
        msg["Subject"] = subject

        content_type = "text/html" if is_html else "text/plain"
        msg.attach(MIMEText(body, content_type))

        return msg

    async def send_email(
        self, to_email: str, subject: str, body: str, is_html: bool = False
    ) -> bool:
        """Send an email.

        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body content
            is_html: Whether body contains HTML

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.settings.smtp_user:
            # SMTP not configured, skip
            return False

        try:
            msg = self._create_message(to_email, subject, body, is_html)

            with smtplib.SMTP(
                self.settings.smtp_host, self.settings.smtp_port
            ) as server:
                server.starttls()
                server.login(
                    self.settings.smtp_user, self.settings.smtp_password
                )
                server.send_message(msg)

            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False

    async def send_morning_briefing(
        self, to_email: str, plan_date: str, tasks_summary: dict
    ) -> bool:
        """Send morning briefing email."""
        body = f"""
        <html>
        <body>
            <h2>Good morning! Here's your plan for {plan_date}</h2>
            <p>You have {tasks_summary['total']} tasks today.</p>
            {self._format_tasks_html(tasks_summary['tasks'])}
            <p>Start with your most important tasks first!</p>
        </body>
        </html>
        """
        return await self.send_email(
            to_email,
            f"Your Plan for {plan_date}",
            body,
            is_html=True,
        )

    async def send_evening_reflection(
        self, to_email: str, plan_date: str, completion_stats: dict
    ) -> bool:
        """Send evening reflection email."""
        body = f"""
        <html>
        <body>
            <h2>Day Complete: {plan_date}</h2>
            <p>You completed {completion_stats['completed']} of {completion_stats['total']} tasks.</p>
            <p>Mood: {completion_stats.get('mood', 'Not set')}</p>
            <p>Reflect on your day and plan for tomorrow!</p>
        </body>
        </html>
        """
        return await self.send_email(
            to_email,
            f"Your Day Summary: {plan_date}",
            body,
            is_html=True,
        )

    def _format_tasks_html(self, tasks: list) -> str:
        """Format tasks as HTML list."""
        if not tasks:
            return "<p>No tasks scheduled.</p>"

        items = "".join(
            f"<li>{t['title']} - {t['priority']}</li>" for t in tasks
        )
        return f"<ul>{items}</ul>"