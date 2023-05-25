#!/usr/bin/python3
""" Name: rhsf.py
 Description: Automates boring Salesforce tasks.
 Platforms: Developed on Fedora 33, tested on RHEL 8 and MacOS
 For details, see: https://gitlab.consulting.redhat.com/nordicssa/salesforce-automation

 A normal salesforce account at redhat.salesforce.com.
 Note: A lot of custom objects, so this doesn't work outside of Red Hat
 Authors: Magnus Glantz, sudo@redhat.com, 2020
          Ilkka Tengvall, ikke@redhat.com, 2020
          Timo Friman, tfriman@redhat.com , 2020 """

# Import required modules
from flask import jsonify,request
import tarfile
import urllib.request
import os
import argparse
from subprocess import call
from subprocess import Popen, PIPE
import subprocess
import sys
import configparser
import shutil
import tempfile
import hashlib
import logging
import platform
import re

try:
    import simplejson as json
except ImportError:
    import json

def rhsf_init():
    # Base directories
    global home_dir, downloads_dir,download_sfdx_file,sf_dir,cwd

    home_dir = os.getenv("HOME")
    downloads_dir = (home_dir+"/Downloads")
    download_sfdx_file = (downloads_dir+"/sfdx-linux-amd64.tar.xz")
    sf_dir = (home_dir+"/salesforce")
    cwd = os.getcwd()

    # Ensure salesforce cli is installed and user is authenticated
    salesforce_prereq(downloads_dir, download_sfdx_file, sf_dir)

def salesforce_prereq(downloads_dir, download_sfdx_file, sf_dir):
    """ Ensure sfdx is installed and that the user is authenticated """
    dev_null = open(os.devnull, 'wb')
    # Download and install the sfdx cli, if it's not already installed
    return_code = subprocess.call(['which', 'sfdx'], stdout=dev_null, stderr=subprocess.STDOUT)
    detected_os = platform.system()
    if return_code != 0:
        print("You do not have the salesforce CLI installed.")
        print("Starting install, this will take a couple of minutes.")

        # If CLI is not yet downloaded, download tar archive
        if not os.path.isfile(download_sfdx_file):
            if detected_os == "Darwin":
                print("You are on MacOS. Install the Salesforce CLI from:\
                       https://developer.salesforce.com/tools/sfdxcli#")
                sys.exit(1)

            dl_url = 'https://developer.salesforce.com/media/salesforce-cli/sfdx/channels/stable/sfdx-linux-x64.tar.gz'
            urllib.request.urlretrieve(dl_url, download_sfdx_file)

        # Extract tar archive to ~/Downloads
        tar = tarfile.open(download_sfdx_file)
        tar.extractall(path=downloads_dir)
        tar.close()

        # Find out what the extracted directory is called
        # it's different from the filename of the archive.
        partial_dir = "sfdx-cli"
        for extr_dir in os.listdir(downloads_dir):
            if extr_dir.find(partial_dir) != -1:
                sfdx_dir_name = extr_dir

        # Call the sfdx installation script
        full_sfdx_dir_name = (downloads_dir+"/"+sfdx_dir_name)
        sfdx_call = ("sudo "+full_sfdx_dir_name+"/install")
        call(sfdx_call, cwd=full_sfdx_dir_name, shell=True)

    # If we have not initialized a project yet, do that
    if not os.path.isdir(sf_dir):
        print("Init: Creating sfdx project.")
        call("sfdx force:project:create -n salesforce", cwd=os.getenv("HOME"), shell=True)

    # Change working directory, to prevent sfdx from bailing out
    os.chdir(sf_dir)

    # Check if we are authenticated, if not, authenticate
    try:
        output = subprocess.check_output(["sfdx", "force:auth:list"], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        output = ""

    if output == "" or b'redhat.com' not in output:
        print("Init: We are not authenticated. Please login via the opened web page.")
        call("sfdx force:auth:web:login --instanceurl https://redhat.my.salesforce.com\
              --setalias redhat", cwd=sf_dir, shell=True)
        call("sfdx config:set defaultusername=redhat", cwd=sf_dir, shell=True)        
    return

def find_forecast_group(product_line):
    if not product_line:
        return ""
    """ Map products with forecast groups """

    # Define lists with products per group.
    # Taken from our Master Product Hierachy
    openshift = ['OpenShift Dedicated',\
                 'OpenShift Enterprise',\
                 'OpenShift Online',\
                 'OpenShift TAM',\
                 'Cloud Suite']
    cloud_infrastructure = ['Ansible',\
                            'OpenStack',\
                            'Platform Fees',\
                            'Platform TAM',\
                            'RHCI',\
                            'RHCI TAM',\
                            'RHEV',\
                            'Virtualization TAM']
    middleware = ['3scale',\
                  'A-MQ',\
                  'BPM Suite',\
                  'BRMS',\
                  'Data Grid',\
                  'Data Virtualization',\
                  'Developer Support',\
                  'Enterprise Application Platform',\
                  'Enterprise Portal Platform',\
                  'Enterprise Web Platform',\
                  'Fuse',\
                  'Fuse Service Works',\
                  'JBoss Communication Platform',\
                  'JBoss Developer Support',\
                  'JBoss Web Server',\
                  'Messaging',\
                  'Middleware Fees',\
                  'Middleware TAM',\
                  'Mobile TAM',\
                  'MRG',\
                  'RHOAR',\
                  'Runtime',\
                  'SOA-P / jBPM',\
                  '']
    mobile = ['RHMAP']
    rhel_satellite_csds = ['Certificate Sys and Directory Serv',\
                           'Red Hat Insights',\
                           'Red Hat Satellite',\
                           'RHEL',\
                           'RHEL w/ Smart Virtualization']
    storage = ['Ceph Software',\
               'Gluster Software',\
               'Storage TAM']

    if product_line in str(openshift):
        forecast_group = "OpenShift"
    elif product_line in str(cloud_infrastructure):
        forecast_group = "Cloud Infrastructure"
    elif product_line in str(middleware):
        forecast_group = "Middleware"
    elif product_line in str(mobile):
        forecast_group = "Mobile"
    elif product_line in str(rhel_satellite_csds):
        forecast_group = "RHEL/Satellite/CS-DS"
    elif product_line in str(storage):
        forecast_group = "Storage"

    return forecast_group

def search_account_opportunities(account_id):
    """ Search for opportunities for a specific account id """
    sfdx_call = ("sfdx force:data:soql:query -q\
                \"SELECT Id,\
                Name,\
                StageName,\
                OpportunityNumber__c,\
                AccountId\
                FROM Opportunity WHERE AccountId = \'"+account_id+"\'\
                AND (NOT StageName LIKE \'Closed%\')\
                AND (NOT StageName LIKE \'Rejected%\')\
                ORDER BY OpportunityNumber__c\"")
    logging.debug('%s', sfdx_call)
    output = subprocess.check_output([sfdx_call], cwd=sf_dir, shell=True).decode()    
    jsonResult = {
        'result': output
    }
    print(jsonResult)
    return jsonify(jsonResult)

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
