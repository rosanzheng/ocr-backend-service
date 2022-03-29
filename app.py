# import tools
import base64
import json
import numpy as np
from cv2 import cv2
import pytesseract
import uuid
import os.path
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import shutil
from datetime import datetime, timedelta
import time, threading
import tempfile
import urllib3
import certifi

# import FLASK
from flask import Flask, render_template, request, Blueprint, flash, url_for, redirect, abort, send_file, send_from_directory
from flask_restplus import Api, Resource, fields, reqparse, inputs
from flask_limiter.util import get_remote_address
from flask_cors import CORS, cross_origin
from flask import jsonify

#import Werkzeug
import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property
werkzeug.secure_filename = werkzeug.utils.secure_filename
from werkzeug import secure_filename
from werkzeug.utils import secure_filename
import werkzeug.middleware.proxy_fix as ProxyFix
from werkzeug.datastructures import FileStorage
from functools import partial

# import methods and functions
from preprocessing import preprocessing
from preprocessing import preprocessing_front
from preprocessing import preprocessing_threshadjust
from preprocessing import preprocessing_back
from front import readData
from front import hasDigit
from front import front
from back import readData
from back import hasDigit
from back import back

# create a master upload folder
UPLOAD_FOLDER = 'files'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# allow only 
ALLOWED_EXTENSIONS = {'jpg', 'png'}

# Pytesseract
pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'

app = Flask(__name__)

CORS(app)

# app Configuration
blueprint = Blueprint('api', __name__, url_prefix='/api')
api = Api(blueprint, doc='/doc/')
app.register_blueprint(blueprint)
API_URL = 'http://0.0.0.0:5000/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['MAX_CONTENT_LENGTH'] = 256 * 1024 * 1024
# app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Api descriptions for swagger
DH_APP_API = Api(app, version="beta", title="DIGITAL HEALTH ONC micro service API", description="Processes an image of a health insurance card into a JSON object", doc='/api-docs/', base_url='/')
DH_APP_API = DH_APP_API.namespace('', description='Backend API')

# defines Parser for both definitions
parser_onc = reqparse.RequestParser()
parser_onc.add_argument('files', type=FileStorage, location='files', dest='files', help="two Image files", required=True, action='append')

@DH_APP_API.route('/processData')
class onc(Resource):
    @cross_origin()
    @DH_APP_API.expect(parser_onc)
    @DH_APP_API.doc(responses={200: 'Success', 404: 'No data found', 400: 'No file found', 422: 'Unprocessable Entity', 423: 'Password-Protected', 429: 'Too many requests'})
    def post(self):
        # Get Parser arguments
        args = parser_onc.parse_args()
        filenamer = args.get("files")
        
        # Create folder for user to upload files
        session_id_number = str(uuid.uuid4())
        user_filepath = "files/"+str(session_id_number)
        os.mkdir(user_filepath)

        # Create a new, unique subfolder subfolder to upload the files if it doesn't exist already
        onc_folder = str(uuid.uuid4())
        new_path = str(UPLOAD_FOLDER)+"/"+str(session_id_number)+"/processData"+str(onc_folder)
        try:
            os.mkdir(new_path)
        except:
            pass

        # If less than two documents were uploaded, produce an error
        if len(filenamer) <= 1:
            cleanup(session_id_number)
            abort(422, description="Add at least two documents")

        # Get all files from the parser and save them to the new folder. Also, append them to a list to keep the order.
        files_order_list = []
        for i in range(0, len(filenamer)):
            filenamer1 = filenamer[i]
            filename = secure_filename(filenamer[i].filename)
            filenamer1.save(os.path.join(new_path, filename))

            filenamer2 = os.path.join(new_path, filename)
            files_order_list.append(filenamer2)

        # Test if all files are Images:
        # for item in files_order_list:
        #     file_type = item.split(".")[-1]
        #     file_type.lower()
        #     if file is not an image, produce error 415
        #     if file_type != "jpg" and file_type != "jpeg"  and file_type != "png":
        #         cleanup(session_id_number)
        #         abort(415, description="Unprocessable Entity, wrong file type.")
        
        if request.method == 'POST':
            dataFront = front(files_order_list[0])
            dataBack = back(files_order_list[1])
            if len(dataBack) == 8:
                ### Index in 0 and 1 are names, so we check for substrings:
                name = dataBack[0].lower()
                surname = dataBack[1].lower()
                insurance = ""
                if len(dataFront) > 0:
                    for f in dataFront:
                        plc = f.lower()
                        if not (name in plc) and not (surname in plc):
                            insurance += f + " "
                    if len(insurance) == 0 and len(dataBack[5]) == 0:
                        insurance = ""
                    elif len(insurance) == 0 and len(dataBack[5]) > 0:
                        insurance = dataBack[5]
                
                responseJson = { 'name': dataBack[0],
                'surname': dataBack[1],
                'birthday': dataBack[2],
                'personalId': dataBack[3],
                'carrierId': dataBack[4],
                'insurance': insurance,
                'cardId': dataBack[6],
                'expirationDate': dataBack[7]}
                cleanup(session_id_number)
                return jsonify(responseJson)
            else:
                cleanup(session_id_number)
                abort(404, description="No data found")

        else:
            cleanup(session_id_number)
            abort(400, description="No file found")

def cleanup(id_number):
    check_dir = "files/"+str(id_number)
    shutil.rmtree(check_dir)

if __name__ == "__main__":
    app.run(host='0.0.0.0')