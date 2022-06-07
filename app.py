from __future__ import print_function
import pyrebase
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from flask import Flask, request, jsonify
import cv2
import imutils
import numpy as np
from urllib.request import urlopen
from tempfile import NamedTemporaryFile

def url_to_image(url, readFlag=cv2.IMREAD_COLOR):
    resp = urlopen(url)
    image = np.asarray(bytearray(resp.read()), dtype="uint8")
    image = cv2.imdecode(image, readFlag)
    return image


app = Flask(__name__)
app.config["DEBUG"] = True

firebase_config = {
    "databaseURL": "",
    "apiKey": "AIzaSyD5tFUS61YB2Cewx4kCHOiKiCWEi8gzg_4",
    "authDomain": "virpa-7ecb4.firebaseapp.com",
    "projectId": "virpa-7ecb4",
    "storageBucket": "virpa-7ecb4.appspot.com",
    "messagingSenderId": "117902734190",
    "appId": "1:117902734190:web:0014183903d11e7a55c77f",
    "measurementId": "G-R4XLDEHT7X"
}

firebase = pyrebase.initialize_app(firebase_config)
cred = credentials.Certificate('key.json')
firebase_admin.initialize_app(cred)

storage = firebase.storage()
db = firestore.client()
users_ref = db.collection('users')

@app.route('/', methods=['GET'])
def home():
    return "<h1>Virpa Image Processing Service Release</h1>"

@app.route('/side', methods=['POST'])
@app.route('/front', methods=['POST'])
def update_record():
    id = request.form.get('id')
    image_name = request.form.get('image_name')
    url = ""
    if request.url_rule.rule == "/front":
        url = storage.child("images/{}/frontBody/{}".format(id, image_name)).get_url(None)
    else:
        url = storage.child("images/{}/besideBody/{}".format(id, image_name)).get_url(None)
    
    image = imutils.url_to_image(url)

    height_image = image.shape[0]
    widht_image = image.shape[1]
    scale = 100 / height_image

    kernel = np.ones((5,5),np.uint8)

    # Image Processing
    image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    image_blurred = cv2.GaussianBlur(image_gray, (9, 9), 0)
    edges = cv2.Canny(image_blurred, 30, 150)
    dilation = cv2.dilate(edges, kernel, iterations = 1)
    image_contours, _ = cv2.findContours(dilation, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    image_contours_sorted = sorted(image_contours, key=cv2.contourArea)
    contours_poly = cv2.approxPolyDP(image_contours_sorted[-1], 3, True)
    boundrect = cv2.boundingRect(contours_poly)
    cv2.rectangle(image, (int(boundrect[0]), int(boundrect[1])), (int(boundrect[0]+boundrect[2]), int(boundrect[1]+boundrect[3])), (0,255,0), 2)
    processed_image_url = ""
    with NamedTemporaryFile() as temp:
        #Extract name to the temp file
        iName = "".join([image_name,".jpg"])
        #Save image to temp file
        cv2.imwrite(iName, image)
        #Storing the image temp file inside the bucket
        if request.url_rule.rule == "/front":
            storage.child("images/{}/frontBody/{}".format(id, "processed" + image_name)).put(iName)
            processed_image_url = storage.child("images/{}/frontBody/{}".format(id, "processed" + image_name)).get_url(None)
        else:
            storage.child("images/{}/besideBody/{}".format(id, "processed" + image_name)).put(iName)
            processed_image_url = storage.child("images/{}/besideBody/{}".format(id, "processed" + image_name)).get_url(None)

    data = {}

    if request.url_rule.rule == "/side":
        data["a"] = boundrect[2] * scale
        data["t"] = boundrect[3] * scale
        data["result"] = processed_image_url
    else:
        data["b"] = boundrect[2] * scale
        data["t"] = boundrect[3] * scale
        data["result"] = processed_image_url
    return jsonify(data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)