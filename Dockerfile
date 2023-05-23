# Use the official Python base image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file
COPY modules.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r modules.txt

# Copy the rest of the application code
COPY . .

# Expose the port the application runs on
EXPOSE 5000

# Start the application
CMD [ "python", "rest-api.py" ]
