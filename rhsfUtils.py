#!/usr/bin/python3
""" Name: rhsfUtils.py
 This is a copy of rhsf.py from https://gitlab.consulting.redhat.com/nordicssa/salesforce-automation
 Description: Automates boring Salesforce tasks.
 
 A normal salesforce account at redhat.salesforce.com.
 Note: A lot of custom objects, so this doesn't work outside of Red Hat
 Authors: Magnus Glantz, sudo@redhat.com, 2020
          Ilkka Tengvall, ikke@redhat.com, 2020
          Timo Friman, tfriman@redhat.com , 2020 """

# Import required modules
from flask import jsonify,Response
import os
from subprocess import call
from subprocess import Popen, PIPE
import subprocess
import logging
try:
    import simplejson as json
except ImportError:
    import json

def rhsf_init():
    # Base directories
    global sf_dir

    home_dir = os.getenv("HOME")    
    sf_dir = (home_dir+"/salesforce")   
    print("Checking if "+sf_dir+" exists") 

    # Ensure salesforce cli is installed and user is authenticated
    #salesforce_prereq(downloads_dir, download_sfdx_file, sf_dir)

    # If we have not initialized a project yet, do that
    if not os.path.isdir(sf_dir):
        print("Init: Creating sfdx project.")
        call("sfdx force:project:create -n salesforce", cwd=os.getenv("HOME"), shell=True)

    # Change working directory, to prevent sfdx from bailing out    
    os.chdir(sf_dir)

def sf_get_task_by_id(task_id):
    """ Search for opportunities for a specific account id """
    logging.debug('entered search_task')
    sfdx_call = ("sfdx data:query -q "
                 "\"SELECT "
                 "Id,OwnerId,Owner.Name,ActivityDate,Status,WhatId,Subject,Description "
                 "FROM Task "
                 "WHERE Id = \'" + task_id + "\'\" "
                 "-r json")
    logging.debug('%s', sfdx_call)
    output = subprocess.check_output([sfdx_call], cwd=sf_dir, shell=True).decode()    
    response = Response(
        response=output,
        status=200,
        mimetype='application/json'
    )
    print(output)
    return response

def create_task(request):    
    """ Create a task """

    # Fetch forecast group based on product
    #forecast_product_group = find_forecast_group(request.json['productLine'])

    sfdx_call = ("sfdx force:data:record:create -s \
                Task -v \"OwnerId=\\\""+request.json['ownerId']+"\\\"\
                Subject=\\\""+request.json['subject']+"\\\"\
                ActivityDate="+request.json['activityDate']+"\
                Status=\\\""+request.json['status']+"\\\"\
                Type=\\\""+request.json['type']+"\\\"\
                Priority=\\\""+request.json['priority']+"\\\"\
                Product_Line1__c=\\\""+request.json['productLine']+"\\\"\
                Forecast_Product_Group__c=\\\""+request.json['productGroup']+"\\\"\
                Hours_Spent__c="+request.json['hoursSpent']+"\
                WhoId="+request.json['contactId']+"\
                WhatId="+request.json['accountId']+"\
                Description=\\\""+request.json['description']+"\\\"\
                recordTypeId=012f2000000ghxtAAA\"")

    print("Creating pre-sales task:")
    print("OwnerId: "+request.json['ownerId']+"\
         | Subject: "+request.json['subject']+"\
         | DueDate: "+request.json['activityDate']+"\
         | Status: "+request.json['status']+"\
         | Type: "+request.json['type']+"\
         | Priority: "+request.json['priority']+ "\
         | Product Line: "+request.json['productLine']+"\
         | Forecast Product Group: "+request.json['productGroup']+"\
         | Hours spent: "+request.json['hoursSpent']+"\
         | ContactId: "+request.json['contactId']+"\
         | AccountId: "+request.json['accountId']+"\
         | Description/comment: "+request.json['description'])
    logging.debug('%s', sfdx_call)

    the_process = Popen(sfdx_call, cwd=sf_dir, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    output, err = the_process.communicate(b"input data")
    return_code = the_process.returncode
    resultStr = ""
    if return_code == 0:
        # Output send as bytes, decode turns it to characters
        # which we then can assemble to a string.
        # We can then split the string in words
        # and search through the output for the task_id.
        ascii_output = output.decode('utf-8')
        output_string = ''.join(ascii_output)
        list_of_words = output_string.split()
        task_id = list_of_words[list_of_words.index('record:') + 1].replace('.', '')
        print('Successfully created task: https://redhat.my.salesforce.com/',task_id,sep='')
        resultStr ='Successfully created task: https://redhat.my.salesforce.com/'+task_id
    else:
        err_ascii = err.decode('utf-8')
        error_output = ''.join(err_ascii)
        print("Failed to create task:", error_output)
        resultStr = 'Failed to create task:'+error_output
    apiResult = {
        'resultCode': return_code,
        'result': resultStr
    }
    return jsonify(apiResult)
