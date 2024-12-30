# Python image as the base
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the application code and requirements file into the container
COPY requirements.txt requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose port and set entrypoint
EXPOSE 5008

# Command to run the application
CMD ["python", "main.py"]
