# Contributing

Thank you for your interest in contributing! Here's how to get started.

## Getting Started

1. Fork the repository and clone your fork
2. Create a branch for your change: `git checkout -b feat/your-feature`
3. Make your changes and test them locally (see below)
4. Push to your fork and open a Pull Request against `main`

## Local Development

**Requirements:** Docker, Docker Compose, a Telegram bot token.

```bash
# Copy the env template and fill in your values
cp .env.example .env

# Create the secrets directory and add your token
mkdir -p secrets
echo "your_bot_token_here" > secrets/telegram_bot_token.txt
chmod 600 secrets/telegram_bot_token.txt

# Build and run
docker compose up --build
```

## Branch Naming

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feat/<name>` | `feat/group-chat-support` |
| Bug fix | `fix/<name>` | `fix/phone-auth-crash` |
| Docs | `docs/<name>` | `docs/update-readme` |

## Commit Style

This project follows [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add group chat support
fix: handle phone numbers without country code
docs: add troubleshooting section
```

## Pull Request Guidelines

- Keep PRs focused on a single change
- Describe *why* the change is needed, not just *what* it does
- If the PR fixes an issue, reference it: `Closes #42`

## Reporting Bugs

Open a [GitHub Issue](../../issues/new/choose) using the bug report template.
For security issues, see [SECURITY.md](SECURITY.md).
