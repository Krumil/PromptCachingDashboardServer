import aiohttp
import time
import os
from typing import Optional
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

class LoggingService:
    def __init__(self):
        self.error_messages = defaultdict(list)
        self.error_count = 0
        self.ERROR_BATCH_SIZE = 10
        self.timers = {}

    def start_timer(self, task_name: str):
        """Start timing a task"""
        self.timers[task_name] = time.monotonic()
        return self.timers[task_name]

    def end_timer(self, task_name: str) -> float:
        """End timing a task and return duration"""
        if task_name not in self.timers:
            return 0
        duration = time.monotonic() - self.timers[task_name]
        del self.timers[task_name]
        return duration

    def clean_message(self, text: str) -> str:
        """Clean and escape message for Telegram"""
        text = text.replace('<', '&lt;').replace('>', '&gt;')
        return text[:4000].strip()  # Telegram has a 4096 char limit

    async def log(self, message: str, send_telegram: bool = True):
        """Log a message to console and optionally to Telegram"""
        print(message)
        if send_telegram:
            await self.send_telegram_message(message)

    async def send_telegram_message(self, message: str):
        """Send a message to Telegram channel"""
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            return
            
        try:
            telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            async with aiohttp.ClientSession() as session:
                async with session.post(telegram_url, json={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text": message,
                    "parse_mode": "HTML"
                }) as response:
                    if response.status != 200:
                        print(f"Failed to send Telegram message: {await response.text()}")
        except Exception as e:
            print(f"Error sending Telegram message: {str(e)}")

    async def add_error(self, error_type: str, identifier: str, detail: str = ""):
        """Add an error and send report if batch size reached"""
        self.error_messages[error_type].append((identifier, detail))
        self.error_count += 1
        
        if self.error_count >= self.ERROR_BATCH_SIZE:
            await self.send_error_report()

    async def send_error_report(self):
        """Send accumulated error report"""
        if not self.error_messages:
            return
            
        message = "❌ Error Report:\n\n"
        for error_type, errors in self.error_messages.items():
            message += f"🔸 {error_type} ({len(errors)} occurrences):\n"
            for identifier, detail in errors[:5]:
                clean_detail = self.clean_message(detail) if detail else "No details available"
                message += f"  - <code>{identifier}</code>\n    └ Details: {clean_detail}\n"
            if len(errors) > 5:
                message += f"  ... and {len(errors) - 5} more\n"
            message += "\n"
        
        await self.send_telegram_message(message)
        self.error_messages.clear()
        self.error_count = 0

# Create a singleton instance
logging_service = LoggingService() 