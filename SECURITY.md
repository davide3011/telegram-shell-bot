# Security Policy

## Supported Versions

This project is actively maintained on the `main` branch.

## Reporting a Vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**

If you discover a security issue, report it privately by opening a
[GitHub Security Advisory](../../security/advisories/new) in this repository.

Include as much detail as possible:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

You will receive a response within 48 hours. If the vulnerability is confirmed,
a fix will be released as soon as possible and you will be credited in the release notes.

## Security Design Notes

This bot is designed to execute arbitrary shell commands on the host machine.
By design it is **not** meant to be exposed to untrusted users.
Please review the authentication configuration carefully before deployment:

- Use `ALLOWED_USER_IDS` and/or `ALLOWED_PHONE_NUMBERS` to restrict access
- Keep your Telegram bot token secret
- Prefer Docker secrets over environment variables for the token
- Run the bot only on networks you trust
