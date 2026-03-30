#!/usr/bin/env python3
"""
A very simple Telegram bot that gives you a remote shell over chat.

The bot authenticates users either by Telegram user ID or by phone number.
If a user is not in the pre-defined list of authorized IDs, they must share
their phone number via the "send contact" button. The number is compared
against a whitelist of authorized phone numbers. Once authenticated, any
subsequent text message from the user will be executed as a shell command
inside the container and the output will be sent back to the chat.

This script is intended as a starting point for your own project. It
demonstrates how to build a remote shell with basic access control.
Use at your own risk - executing arbitrary commands can be dangerous.

Environment variables:
    TELEGRAM_BOT_TOKEN: token of your Telegram bot (mandatory).
    TELEGRAM_BOT_TOKEN_FILE: path to file containing the token (preferred for secrets).
    ALLOWED_USER_IDS: comma-separated list of Telegram user IDs allowed
                      to access without phone verification (optional).
    ALLOWED_USER_IDS_FILE: path to file containing ALLOWED_USER_IDS (optional).
    ALLOWED_PHONE_NUMBERS: comma-separated list of allowed phone numbers,
                           configured as digits only (example: 393311234567).
    ALLOWED_PHONE_NUMBERS_FILE: path to file containing ALLOWED_PHONE_NUMBERS (optional).
    COMMAND_TIMEOUT_SECONDS: max command runtime in seconds (optional, default: 300).

Run with:
    python bot.py

When running inside Docker you can expose the container's /var/run/docker.sock
to allow commands such as `docker compose up -d` to control host containers:
    docker run -d --env TELEGRAM_BOT_TOKEN=... --env ALLOWED_PHONE_NUMBERS=391234567890 \
        -v /var/run/docker.sock:/var/run/docker.sock <image>

"""

import logging
import os
import subprocess
from typing import Dict, Optional, Set, Tuple

from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)

# Configure basic logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def get_env_or_file(name: str, default: Optional[str] = None) -> Optional[str]:
    """Return value from env var or from a companion *_FILE env var."""
    file_env_name = f"{name}_FILE"
    file_path = os.getenv(file_env_name)
    if file_path:
        try:
            with open(file_path, "r", encoding="utf-8") as file_handle:
                return file_handle.read().strip()
        except OSError as exc:
            raise RuntimeError(
                f"Unable to read secret file for {name} at '{file_path}': {exc}"
            ) from exc

    value = os.getenv(name)
    if value is None:
        return default
    return value.strip()


def parse_id_list(value: str) -> Set[int]:
    """Parse a comma-separated string of integers into a set."""
    result: Set[int] = set()
    if not value:
        return result
    for item in value.split(','):
        item = item.strip()
        if not item:
            continue
        try:
            result.add(int(item))
        except ValueError:
            logger.warning("Skipping invalid user ID %s", item)
    return result


def parse_phone_list(value: str) -> Set[str]:
    """Parse a comma-separated list of phone numbers into a set.

    Configure whitelist values as digits only. Input received from Telegram
    may include '+' or spaces, so numbers are normalized during matching.
    To improve matching accuracy, only digits are retained when checking
    numbers. Country codes are not stripped here; matching happens by suffix
    to handle local differences.
    """
    result: Set[str] = set()
    if not value:
        return result
    for item in value.split(','):
        digits = ''.join(ch for ch in item if ch.isdigit())
        if digits:
            result.add(digits)
    return result


class ShellBot:
    """A Telegram bot that executes shell commands after authenticating users."""

    def __init__(self, token: str, allowed_user_ids: Set[int], allowed_phones: Set[str]):
        self.allowed_user_ids = allowed_user_ids
        self.allowed_phones = allowed_phones
        self.cwd_marker = "__BOT_CWD_MARKER__"
        self.default_cwd = os.getcwd()
        # Keep track of authorized users for the current session
        self.authorised_users: Set[int] = set()
        # Persist each authorized user's current working directory.
        self.user_cwds: Dict[int, str] = {}
        # Prefer bash for terminal-like behavior; fallback to sh if unavailable.
        self.shell_executable = "/usr/local/bin/hostbash" if os.path.exists("/usr/local/bin/hostbash") else ("/bin/bash" if os.path.exists("/bin/bash") else "/bin/sh")
        self.command_timeout = self._read_command_timeout()

        # Create updater and dispatcher
        self.updater = Updater(token=token, use_context=True)
        self.dispatcher = self.updater.dispatcher
        # Register handlers
        self.dispatcher.add_handler(CommandHandler("start", self.handle_start))
        self.dispatcher.add_handler(MessageHandler(Filters.contact, self.handle_contact))
        # Handle text messages that are not commands
        self.dispatcher.add_handler(
            MessageHandler(Filters.text & ~Filters.command, self.handle_command)
        )

    def _read_command_timeout(self) -> int:
        """Read command timeout from env with safe fallback."""
        raw_value = os.getenv("COMMAND_TIMEOUT_SECONDS", "300").strip()
        try:
            timeout = int(raw_value)
            if timeout <= 0:
                raise ValueError("timeout must be > 0")
            return timeout
        except ValueError:
            logger.warning(
                "Invalid COMMAND_TIMEOUT_SECONDS '%s'. Falling back to 300.",
                raw_value,
            )
            return 300

    def _normalize_command(self, text: str) -> str:
        """Normalize plain text or fenced code block input to raw command text."""
        cmd = text.strip()
        if cmd.startswith("```") and cmd.endswith("```"):
            lines = cmd.splitlines()
            if len(lines) >= 2:
                # Drop opening fence (with optional language) and closing fence.
                cmd = "\n".join(lines[1:-1]).strip()
        return cmd

    def _extract_output_and_cwd(self, output: str) -> Tuple[str, Optional[str]]:
        """Extract visible output and tracked working directory marker."""
        marker_index = output.rfind(self.cwd_marker)
        if marker_index == -1:
            return output, None

        visible_output = output[:marker_index].rstrip()
        marker_payload = output[marker_index + len(self.cwd_marker):].strip()
        updated_cwd = marker_payload.splitlines()[0].strip() if marker_payload else None
        return visible_output, updated_cwd

    def handle_start(self, update: Update, context: CallbackContext) -> None:
        """Send a greeting and request contact if not already authorized."""
        user = update.effective_user
        user_id = user.id if user else None
        # If user ID is whitelisted or previously authorized, skip contact request
        if user_id in self.allowed_user_ids or user_id in self.authorised_users:
            self.authorised_users.add(user_id)
            if user_id is not None and user_id not in self.user_cwds:
                self.user_cwds[user_id] = self.default_cwd
            update.message.reply_text(
                "You are already authorized. Send a command to run in the shell."
            )
            return

        # Ask for contact to verify phone number
        button = KeyboardButton("Share your phone number", request_contact=True)
        markup = ReplyKeyboardMarkup([[button]], one_time_keyboard=True)
        update.message.reply_text(
            "Please authorize by sharing your phone number.",
            reply_markup=markup,
        )

    def handle_contact(self, update: Update, context: CallbackContext) -> None:
        """Process a contact message to verify the user's phone number."""
        message = update.message
        contact = message.contact
        user_id = update.effective_user.id if update.effective_user else None
        # Sanity check: ensure the contact belongs to the sender
        if contact is None or contact.user_id != user_id:
            message.reply_text("Error: please use the button to share your number.")
            return

        phone_number = contact.phone_number or ''
        digits = ''.join(ch for ch in phone_number if ch.isdigit())
        # Compare by suffix: any allowed number that is a suffix of the provided
        # number counts as a match. This accommodates country codes.
        matched: bool = False
        for allowed in self.allowed_phones:
            if digits.endswith(allowed):
                matched = True
                break

        if matched:
            self.authorised_users.add(user_id)
            if user_id is not None and user_id not in self.user_cwds:
                self.user_cwds[user_id] = self.default_cwd
            message.reply_text(
                "Authentication successful. You can now send shell commands."
            )
            logger.info("User %s authorized via phone number %s", user_id, phone_number)
        else:
            message.reply_text("Phone number not authorized. Access denied.")
            logger.warning(
                "Unauthorized phone number attempt from user %s: %s",
                user_id,
                phone_number,
            )

    def handle_command(self, update: Update, context: CallbackContext) -> None:
        """Execute a shell command if the user is authorized."""
        user_id = update.effective_user.id if update.effective_user else None
        # Check if the user is authorized
        if user_id not in self.allowed_user_ids and user_id not in self.authorised_users:
            update.message.reply_text("You are not authorized. Use /start to authenticate.")
            return

        cmd = self._normalize_command(update.message.text)
        if not cmd:
            return

        logger.info("Executing command from user %s: %s", user_id, cmd)

        start_cwd = self.user_cwds.get(user_id, self.default_cwd) if user_id is not None else self.default_cwd
        if not os.path.isdir(start_cwd):
            start_cwd = self.default_cwd

        wrapped_cmd = (
            f"{cmd}\n"
            "cmd_status=$?\n"
            f"printf '\\n{self.cwd_marker}%s\\n' \"$PWD\"\n"
            "exit $cmd_status\n"
        )

        proc: Optional[subprocess.Popen] = None
        try:
            # Run commands through bash -lc for terminal-like behavior.
            proc = subprocess.Popen(
                [self.shell_executable, "-lc", wrapped_cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=start_cwd,
            )
            # Collect output with a timeout to prevent hanging commands.
            output, _ = proc.communicate(timeout=self.command_timeout)
            output, updated_cwd = self._extract_output_and_cwd(output)
            if user_id is not None and updated_cwd:
                self.user_cwds[user_id] = updated_cwd
        except subprocess.TimeoutExpired:
            if proc is not None:
                proc.kill()
            output = (
                "Command terminated due to timeout after "
                f"{self.command_timeout} seconds."
            )
        except Exception as exc:
            output = f"Error while executing command: {exc}"

        # If there is no output, send a placeholder message.
        if not output.strip():
            output = "Command executed with no output."

        # Telegram messages have a maximum length of 4096 characters; split if necessary.
        chunk_size = 4000
        for i in range(0, len(output), chunk_size):
            update.message.reply_text(output[i:i + chunk_size])

    def run(self) -> None:
        """Start the bot."""
        self.updater.start_polling()
        logger.info("Bot started and polling for messages.")
        self.updater.idle()


def main() -> None:
    token = get_env_or_file('TELEGRAM_BOT_TOKEN')
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN (or TELEGRAM_BOT_TOKEN_FILE) is not set.")

    allowed_user_ids = parse_id_list(get_env_or_file('ALLOWED_USER_IDS', '') or '')
    allowed_phones = parse_phone_list(get_env_or_file('ALLOWED_PHONE_NUMBERS', '') or '')

    bot = ShellBot(token, allowed_user_ids, allowed_phones)
    bot.run()


if __name__ == '__main__':
    main()
