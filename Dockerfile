# Use the official Python base image (Python 3.12-slim for smaller image size)
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Set environment variables
# Prevents Python from writing .pyc files to disc
ENV PYTHONDONTWRITEBYTECODE=1
# Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1

# Install system dependencies (required for some Python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements.txt first to leverage Docker's layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to the container
COPY . .

# Expose the port where the Flask app will run (default for run.py is 5000)
EXPOSE 5000

# Start the application
# We'll use the entry point run.py as it seems to be the main starting script
CMD ["python", "run.py"]
