from flask import Flask, jsonify, request
from flask_httpauth import HTTPTokenAuth
# importing  all the functions defined in rhsfUtils.py
from rhsfUtils import *
import os

app = Flask(__name__)
auth = HTTPTokenAuth(scheme='Bearer')

tokens ={}

strHWResult = {
    'result' : 'Hello World !!!'
}

#Authentication Utils
def load_auth_tokens():
    tokenString = os.environ.get('AUTH_TOKEN_SECRET')

    global tokens # Need to update global varaibles
    tokens = json.loads(tokenString)

@auth.verify_token
def verify_token(token):
    if token in tokens:
        return tokens[token]

# Test Endpoint
@app.route('/hw')
@auth.login_required
def hello():
    result = "Hello {}!!!".format(auth.current_user())    
    return jsonify({'result':result})

# SFDW Read operation endpoint - Get Task Details By ID
@app.route('/sfdw/getTaskByID/<string:id>', methods=['GET'])
@auth.login_required
def get_task_by_id(id):
    return sf_get_task_by_id(id)

# SFDW Write operation endpoint - Create Task
@app.route('/sfdw/createTask',methods=['POST'])
@auth.login_required
def createTask():
    return create_task(request)
    

if __name__ == '__main__':
    load_auth_tokens()
    #rhsf_init()

    port = os.environ.get('FLASK_PORT') or 8080
    port = int(port)

    app.run(port=port,host='0.0.0.0')