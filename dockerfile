# Use a Python base image
FROM python:3.11-slim

# Set environment variables to prevent Python from writing .pyc files 
# and ensure output is unbuffered
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install PostgreSQL client and other dependencies (needed to build psycopg2)
RUN apt-get update 
# && apt-get install -y --no-install-recommends \
# postgresql-client \
# gcc \
# python3-dev \
# musl-dev \
# && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /usr/src/app

# Install Python dependencies
COPY requirements.txt .
# Install psycopg2-binary for local development
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the Django project files
COPY . .

RUN python3 manager.py spectacular --color --file "schema.yml"
# Expose the Gunicorn/Django server port
EXPOSE 8000

# Command to run the Django development server
# NOTE: In production, you would use Gunicorn or a similar WSGI server.
CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"] 
