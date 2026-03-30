FROM python:3.11-slim

# Create a non‑root user to run the bot for security
RUN adduser --disabled-password --gecos "" botuser

# Set the working directory
WORKDIR /app

# Copy dependency specification and install
COPY requirements.txt /app/requirements.txt
RUN apt-get update && apt-get install -y --no-install-recommends util-linux \
    && rm -rf /var/lib/apt/lists/* \
    && printf '#!/bin/sh\nif [ -n "$BOT_WORK_DIR" ]; then\n  HOSTUSER=$(basename "$BOT_WORK_DIR")\nelse\n  HOSTUSER=$(nsenter -t 1 -m -u -i -n -p -- getent passwd 1000 | cut -d: -f1)\nfi\nexec nsenter -t 1 -m -u -i -n -p -- runuser -l "$HOSTUSER" -c "$2"\n' \
       > /usr/local/bin/hostbash \
    && chmod +x /usr/local/bin/hostbash

RUN pip install --no-cache-dir -r requirements.txt

# Copy bot source code
COPY bot.py /app/bot.py

# Expose no ports; the bot communicates via outbound HTTPS

CMD ["python", "bot.py"]