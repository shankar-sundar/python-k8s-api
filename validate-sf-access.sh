#!/bin/bash

# Specify the file path to check
file_path="/tmp/.sfdx/key.json"
#api_endpoint="https://python-sf-api-gsisa.apps.hou.edgelab.online"
api_endpoint="http://127.0.0.1:8080"

bearer_token=$(echo $AUTH_TOKEN_SECRET | jq -r 'to_entries[] | select(.value == "'"admin"'") | .key')


# Check if the file exists
if [ -f "$file_path" ]; then
    echo "File exists at $file_path"
    
    # Change permissions of the file to 600
    chmod 600 "$file_path"
    echo "Changed permissions of $file_path to 600"
    #sleep 10
    
    # Make the GET request and store the response status code in a variable    
    response=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $bearer_token" "$api_endpoint/sfdw/getTaskByID/00T3a00005lqDkX")

    # Check the response status code
    if [ "$response" -eq 200 ]; then
        echo "GET request successful (HTTP 200)"        
    else
        echo "GET request failed with status code: $response"
        exit -1
    fi
else
    echo "File does not exist at $file_path"
    exit -1
fi