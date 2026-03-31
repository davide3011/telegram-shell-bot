# Telegram SBC Remote Control Bot

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](Dockerfile)

A Dockerized Telegram bot for remotely controlling single-board computers (SBCs)
like Raspberry Pi, Orange Pi, and Odroid without opening inbound ports or configuring
router port forwarding.

The bot uses Telegram long polling, so the SBC only needs outbound HTTPS access.
No public endpoint is exposed.

## Why This Project

Use this project when you need to:
- run remote shell commands on SBCs behind NAT/firewalls;
- manage distributed edge devices without exposing SSH to the internet;
- perform quick operational tasks without VPN or port forwarding.

## How It Works (No Port Forwarding)

1. The container runs the bot on your SBC.
2. The bot polls Telegram APIs for new messages.
3. Authorized users send commands in Telegram chat.
4. Commands run inside the container and output is returned in chat.

## Security Model

Two authentication methods are supported:
- `ALLOWED_USER_IDS`: trusted Telegram user IDs with immediate access.
- `ALLOWED_PHONE_NUMBERS`: trusted phone numbers (digits only) verified through Telegram contact sharing.

Important behavior:
- At least one whitelist must be configured, otherwise nobody can authenticate.
- If both are configured, user ID whitelist is checked first.
- The bot executes arbitrary shell commands, so use only with trusted users.

## Prerequisites

- A Telegram account.
- Docker Engine and Docker Compose plugin installed on the SBC.
- Outbound internet connectivity from the SBC.

Quick check:

```bash
docker --version
docker compose version
```

## Step 1 - Create Your Telegram Bot (BotFather)

1. Open Telegram and search for `@BotFather`.
2. Send `/start`.
3. Send `/newbot`.
4. Enter a display name (example: `SBC Control Bot`).
5. Enter a unique username ending in `bot` (example: `my_sbc_control_bot`).
6. BotFather returns a token in this format: `123456789:AA...`.
7. Copy and store this token securely. You will use it as a local secret.

Optional but recommended:
- `/setdescription` to set the bot description.
- `/setuserpic` to set a bot avatar.
- `/setcommands` to define commands (for example `start`).

## Step 2 - Choose an Authentication Mode

### Option A (Recommended): Telegram user ID whitelist

1. Get your Telegram user ID (for example with `@userinfobot`).
2. Put it in `ALLOWED_USER_IDS`.
3. Leave `ALLOWED_PHONE_NUMBERS` empty if you do not need phone fallback.

### Option B: Phone whitelist only

1. Put your number in `ALLOWED_PHONE_NUMBERS` using digits only (example: `391234567890`).
2. Leave `ALLOWED_USER_IDS` empty.
3. On first access, send `/start` and share your contact when prompted.

Phone format rule (important):
- Use digits only.
- Valid examples: `393311234567`, `3311234567`.
- Invalid examples: `+39 331 123 4567`, `(+39)331-123-4567`.

## Step 3 - Configure the Project

Run commands from the project folder.

1. Create the environment file:

```bash
cp .env.example .env
```

2. Create the bot token secret file:

```bash
mkdir -p secrets
printf '%s' 'PASTE_YOUR_BOT_TOKEN_HERE' > secrets/telegram_bot_token.txt
chmod 600 secrets/telegram_bot_token.txt
```

3. Edit `.env` according to your authentication mode.

Example (user ID only):

```env
ALLOWED_USER_IDS=123456789
ALLOWED_PHONE_NUMBERS=
```

Example (phone only):

```env
ALLOWED_USER_IDS=
ALLOWED_PHONE_NUMBERS=391234567890
```

You can configure multiple phone numbers separated by commas:

```env
ALLOWED_PHONE_NUMBERS=393311234567,393491112233
```

## Step 4 - Start the Service

```bash
docker compose up -d --build
```

Check status and logs:

```bash
docker compose ps
docker compose logs -f
```

The service uses `restart: unless-stopped`, so it starts automatically after host reboot
or Docker daemon restart.

## Step 5 - First Login and Test

1. Open your bot chat in Telegram.
2. Send `/start`.
3. If your ID is in `ALLOWED_USER_IDS`, access is immediate.
4. If phone whitelist mode is used, share your contact when asked.
5. Send a test command, for example:

```text
uname -a
```

## Operational Notes

- The compose file mounts `/var/run/docker.sock` into the container.
- This allows executing Docker commands on the host from Telegram.
- If this is not required, remove that volume mapping from `docker-compose.yml`.

## Sensitive Data Handling

- Bot token is provided as a Docker secret at `/run/secrets/telegram_bot_token`.
- Never commit `.env` or anything under `secrets/`.
- Keep strict permissions on the token file (`chmod 600`).
- Rotate the token with BotFather (`/revoke`) if exposure is suspected.

## Update Procedure

```bash
docker compose down
docker compose up -d --build
```

## Contributing

Contributions, bug reports, and feature requests are welcome.
See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
To report a security vulnerability, follow the [SECURITY.md](SECURITY.md) policy.

## Troubleshooting

- `TELEGRAM_BOT_TOKEN ... not set`:
  check `secrets/telegram_bot_token.txt` and the secret mapping in `docker-compose.yml`.
- `You are not authorized` message:
  check whitelist values in `.env` and restart with `docker compose up -d`.
- Bot does not respond:
  verify outbound internet access and inspect logs with `docker compose logs -f`.
- Compose error about missing `.env`:
  create it from `.env.example`.
