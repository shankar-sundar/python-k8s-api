# Red Hat SalesForce automation (rhsf)

CLI to automate boring Salesforce tasks.

# Installing on Fedora/RHEL
```
# Download rhsf.py
chmod a+rx rhsf.py
sudo cp rhsf.py /usr/local/bin/rhsf
```

# Installing on MacOS
```
# Install brew
brew install python
#alias python=/usr/local/bin/python3
alias python=/opt/homebrew/bin/python3
# Download rhsf.py
chmod a+rx rhsf.py
sudo cp rhsf.py /usr/local/bin/rhsf
```

There is a bug in OSX sfdc install, you may need to do this also:
```
sudo xcode-select --reset
```

# Container version

## Build
To build the Containerized version, you need to:
```
podman build .
```

export CONTAINER_ID=<containerid>
export REDHAT_EMAIL=<emailid>
export AUTH_TOKEN_SECRET='{"secret-1":"admin"}'

## Configure
To setup the environment properly, execute the following commands, using the proper `CONTAINER_ID` and `REDHAT_EMAIL`:
```
podman volume create sfdx
podman run -p 8080:8080 --rm -v sfdx:/root:Z $CONTAINER_ID sfdx force:auth:device:login --instance-url https://redhat.my.salesforce.com --alias redhat
podman run -p 8080:8080 --rm -v sfdx:/root:Z $CONTAINER_ID sfdx force:project:create -n salesforce
podman run -p 8080:8080 --rm -v sfdx:/root:Z $CONTAINER_ID bash -c "cd salesforce && sfdx config:set defaultusername=$REDHAT_EMAIL"
```

podman run -p 8080:8080 -e HOME=/Users/sankara/temp -e AUTH_TOKEN_SECRET='{"secret-1":"admin"}' --rm -v sfdx:/root:Z $CONTAINER_ID


### openshift

One time setup
1. sfdx force:auth:device:login --instance-url https://redhat.my.salesforce.com --alias redhat
2. cd /tmp/salesforce 
3. sfdx config:set defaultusername=<username>
4. chmod 600 /tmp/.sfdx/key.json