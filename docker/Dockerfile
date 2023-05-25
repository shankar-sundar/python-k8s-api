FROM registry.access.redhat.com/ubi9/ubi-init

RUN dnf -y install nodejs git jq gettext python3-pip
#RUN dnf -y install which nodejs git jq gettext xmlstarlet python3-pip

RUN npm install sfdx-cli --global
RUN sfdx --version
RUN sfdx plugins --core

# By default, listen on port 8081
EXPOSE 8080/tcp
ENV FLASK_PORT=8080

# Set the working directory in the container
WORKDIR /root
VOLUME ["/root"]

# Copy the requirements file
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Start the application
CMD [ "python3", "app.py" ]
