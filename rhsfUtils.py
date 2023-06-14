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
import re
try:
    import simplejson as json
except ImportError:
    import json

os.system("")

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
    """ Search for task by id """
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

def sf_get_opportunity(opportunity_id,opportunity_number):
    """ Search for opportunities for a given id """
    logging.debug('entered search_opportunity')
    whereClause = "WHERE "
    if opportunity_id == "" and opportunity_number == "":
        return Response(response={
            "result":"failed",
            "errors":"Missing opportunity ID or number to find opportunity"
        },
        status=500,
        mimetype='application/json')
    
    if opportunity_id == "":
        whereClause += "opportunitynumber__c = \'"+opportunity_number+ "\'\" "
    else:
        whereClause += "Id = \'" + opportunity_id + "\'\" "

    sfdx_query = "sfdx data:query -q "+"\"SELECT "+"Id,Name,opportunitynumber__c,StageName,AccountId,closedate,Amount "+ "FROM Opportunity "+whereClause+" -r json"        
    sfdx_call = (sfdx_query)
    logging.debug('%s', sfdx_call)
    output = subprocess.check_output([sfdx_call], cwd=sf_dir, shell=True).decode()    
    response = Response(
        response=output,
        status=200,
        mimetype='application/json'
    )
    print(output)
    return response

def validate_incoming_payload(payload):
    errorList = []
    mandatoryFields = ['ownerId','subject','activityDate','status','type','priority','productLine','productGroup','hoursSpent','contactId','accountId','description']

    for fieldName in mandatoryFields:
        if not mandatory_check(payload,fieldName):
            errorList.append("Missing "+fieldName)    

    if len(errorList) > 0:
        print("Validation failed with errors ")
        print(errorList)

    return errorList

def mandatory_check(payload,field):    
    if field not in payload:                
        return False
    else:
        return True

def create_task(request):
    payload = request.json
    errorList = validate_incoming_payload(payload)    
    if len(errorList) == 0:  
        try:      
            return create_task_sfdx(payload)
        except Exception as e:
            return form_response(callSuccessful=False,
                                taskURL="",
                                errors="Failed while calling sfdx "+str(e),
                                payload=payload)
    else:                       
        return form_response(callSuccessful=False,
                            taskURL="",
                            errors=errorList,
                            payload=payload)

def escape_ansi(line):
    ansi_escape =re.compile(r'(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]')
    return ansi_escape.sub('', line)    

def create_task_sfdx(payload):    
    """ Create a task """

    # Fetch forecast group based on product
    #forecast_product_group = find_forecast_group(payload['productLine'])694589


    sfdx_call = ("sfdx force:data:record:create -s \
                Task -v \"OwnerId=\\\""+payload['ownerId']+"\\\"\
                Subject=\\\""+payload['subject']+"\\\"\
                ActivityDate="+payload['activityDate']+"\
                Status=\\\""+payload['status']+"\\\"\
                Type=\\\""+payload['type']+"\\\"\
                Priority=\\\""+payload['priority']+"\\\"\
                Product_Line1__c=\\\""+payload['productLine']+"\\\"\
                Forecast_Product_Group__c=\\\""+payload['productGroup']+"\\\"\
                Hours_Spent__c="+payload['hoursSpent']+"\
                WhoId="+payload['contactId']+"\
                WhatId="+payload['accountId']+"\
                Description=\\\""+payload['description']+"\\\"\
                recordTypeId=012f2000000ghxtAAA\"")

    print("Creating pre-sales task:")
    print("OwnerId: "+payload['ownerId']+"\
         | Subject: "+payload['subject']+"\
         | DueDate: "+payload['activityDate']+"\
         | Status: "+payload['status']+"\
         | Type: "+payload['type']+"\
         | Priority: "+payload['priority']+ "\
         | Product Line: "+payload['productLine']+"\
         | Forecast Product Group: "+payload['productGroup']+"\
         | Hours spent: "+payload['hoursSpent']+"\
         | ContactId: "+payload['contactId']+"\
         | AccountId: "+payload['accountId']+"\
         | Description/comment: "+payload['description'])
    logging.debug('%s', sfdx_call)

    the_process = Popen(sfdx_call, cwd=sf_dir, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    output, err = the_process.communicate(b"input data")
    return_code = the_process.returncode    
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
        return form_response(callSuccessful=True,
                            taskURL="https://redhat.my.salesforce.com/"+task_id,
                            errors="",
                            payload="")
    else:
        err_ascii = escape_ansi(err.decode('utf-8'))
        error_output = ''.join(err_ascii)
        print(error_output)        
        readableOut = ' '.join(re.findall(r'\w+', error_output))
        return form_response(callSuccessful=False,
                            taskURL="",
                            errors="Failed while creating task in SF - "+readableOut,
                            payload=payload)    
        
def form_response(callSuccessful,taskURL,errors,payload):        
    apiResult = {}
    status = 200   
    if not callSuccessful:
        status = 500
        apiResult = {            
            'result': 'failed',         
            'taskURL': '',
            'errors': errors,
            'payload':payload
        }    
    else:
        apiResult = {            
            'result': 'success',         
            'taskURL': taskURL,
            'errors': '',
            'payload':''
        }    

    print("api response to client")
    print(apiResult)

    return Response(
            response=json.dumps(apiResult),
            status=status,
            mimetype='application/json'
        )
