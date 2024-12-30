# Python image as the base
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y iputils-ping

# Copy the application code and requirements file into the container
COPY main.py /app/
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the app runs on
EXPOSE 5002

# Command to run the application
CMD ["python", "main.py"]

