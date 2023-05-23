FROM registry.access.redhat.com/ubi9/python-39:1-108

# By default, listen on port 8081
EXPOSE 8080/tcp
ENV FLASK_PORT=8080

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Start the application
CMD [ "python", "rest-api.py" ]
