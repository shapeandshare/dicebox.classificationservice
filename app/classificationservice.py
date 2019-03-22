#!flask/bin/python
###############################################################################
# Classification Service
#   Handles requests for classification of data from a client.
#
# Copyright (c) 2017-2019 Joshua Burt
###############################################################################


###############################################################################
# Dependencies
###############################################################################
import lib.docker_config as config
from flask import Flask, jsonify, request, make_response, abort
from flask_cors import CORS, cross_origin
import base64
from lib.network import Network
import logging
import json


###############################################################################
# Setup logging.
###############################################################################
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p',
    level=logging.DEBUG,
    filemode='w',
    filename="%s/classificationservice.log" % config.LOGS_DIR
)


###############################################################################
# Create the network.
###############################################################################
network = Network(config.NN_PARAM_CHOICES)


###############################################################################
# Load categories for the model
###############################################################################
with open('%s/category_map.json' % config.WEIGHTS_DIR) as data_file:
    jdata = json.load(data_file)
server_category_map = {}
for d in jdata:
    server_category_map[str(jdata[d])] = str(d)
logging.info('loaded categories: %s' % server_category_map)


###############################################################################
# Create the flask, and cors config
###############################################################################
app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "http://localhost:*"}})


###############################################################################
# Method call that creates the classification response.
# We are loading a specific model (lonestar), with a pre-created weights file.
# Here we elect to create_model, which will also load the model weights on
# first use.
###############################################################################
def get_classification(image_data):
    try:
        network.create_lonestar(create_model=True,
                                weights_filename="%s/%s" % (config.WEIGHTS_DIR, config.MODEL_WEIGHTS_FILENAME))
    except:
        logging.error('Error summoning lonestar')
        return -1

    classification = network.classify(image_data)
    logging.info("classification: (%s)" % classification)
    return classification[0]

# We need more specificity before we start catching stuff here, otherwise this
# catches too many issues.
#
#    try:
#        classification = network.classify(image_data)
#        logging.info("classification: (%s)" % classification)
#        return classification[0]
#    except:
#        logging.error('Error making prediction..')
#        return -1


###############################################################################
# Provides categories for client consumption
###############################################################################
@app.route('/api/categories', methods=['GET'])
def make_api_categorymap_public():
    if request.headers['API-ACCESS-KEY'] != config.API_ACCESS_KEY:
        abort(403)
    if request.headers['API-VERSION'] != config.API_VERSION:
        abort(400)

    return make_response(jsonify({'category_map': server_category_map}), 200)


###############################################################################
# Endpoint which provides classification of image data.
###############################################################################
@app.route('/api/classify', methods=['POST'])
def make_api_get_classify_public():
    if request.headers['API-ACCESS-KEY'] != config.API_ACCESS_KEY:
        abort(403)
    if request.headers['API-VERSION'] != config.API_VERSION:
        abort(400)
    if not request.json:
        abort(400)
    if 'data' in request.json and type(request.json['data']) != unicode:
        abort(400)

    encoded_image_data = request.json.get('data')
    decoded_image_data = base64.b64decode(encoded_image_data)
    classification = get_classification(decoded_image_data)

    return make_response(jsonify({'classification': classification}), 200)


###############################################################################
# Returns API version
###############################################################################
@app.route('/api/version', methods=['GET'])
def make_api_version_public():
    return make_response(jsonify({'version':  str(config.API_VERSION)}), 200)


###############################################################################
# Super generic health end-point
###############################################################################
@app.route('/health/plain', methods=['GET'])
@cross_origin()
def make_health_plain_public():
    return make_response('true', 200)


###############################################################################
# 404 Handler
###############################################################################
@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


###############################################################################
# main entry point, thread safe
###############################################################################
if __name__ == '__main__':
    logging.debug('starting flask app')
    app.run(debug=config.FLASK_DEBUG, host=config.LISTENING_HOST, threaded=True)
