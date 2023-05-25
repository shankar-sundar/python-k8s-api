from flask import Flask, jsonify, request 
# importing  all the functions defined in rhsfUtils.py
from rhsfUtils import *
import os

app = Flask(__name__)

strHWResult = {
    'result' : 'Hello World !!!'
}


@app.route('/hw')
def hello():
    return jsonify(strHWResult)

@app.route('/sfdw/listOppByAcctID/<string:id>', methods=['GET'])
def list_opportunities_by_id(id):
    return search_account_opportunities(id)

@app.route('/sfdw/createTask',methods=['POST'])
def createTask():
    return create_task(request)
    

if __name__ == '__main__':
    rhsf_init()

    port = os.environ.get('FLASK_PORT') or 8080
    port = int(port)

    app.run(port=port,host='0.0.0.0')