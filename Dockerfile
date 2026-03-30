FROM python:3.11-slim

# Create a non‑root user to run the bot for security
RUN adduser --disabled-password --gecos "" botuser

# Set the working directory
WORKDIR /app

# Copy dependency specification and install
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot source code
COPY bot.py /app/bot.py

# Use an unprivileged user
USER botuser

# Expose no ports; the bot communicates via outbound HTTPS

CMD ["python", "bot.py"]