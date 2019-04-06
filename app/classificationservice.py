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
from flask import Flask, jsonify, request, make_response, abort
from flask_cors import CORS, cross_origin
import base64
import logging
import json
import os
import errno
from dicebox.config.dicebox_config import DiceboxConfig
from dicebox.dicebox_network import DiceboxNetwork

# Config
config_file = './dicebox.config'
CONFIG = DiceboxConfig(config_file)


###############################################################################
# Allows for easy directory structure creation
# https://stackoverflow.com/questions/273192/how-can-i-create-a-directory-if-it-does-not-exist
###############################################################################
def make_sure_path_exists(path):
    try:
        if os.path.exists(path) is False:
            os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


###############################################################################
# Setup logging.
###############################################################################
make_sure_path_exists(CONFIG.LOGS_DIR)
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p',
    level=logging.DEBUG,
    filemode='w',
    filename="%s/classificationservice.%s.log" % (CONFIG.LOGS_DIR, os.uname()[1])
)


###############################################################################
# Create the network. (Create FSC, disabling data indexing)
###############################################################################
network = DiceboxNetwork(CONFIG.NN_PARAM_CHOICES, True, True, config_file)


###############################################################################
# Load categories for the model
###############################################################################
with open('%s/category_map.json' % CONFIG.WEIGHTS_DIR) as data_file:
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
                                weights_filename="%s/%s" % (CONFIG.WEIGHTS_DIR, CONFIG.MODEL_WEIGHTS_FILENAME))
    except:
        logging.error('Error summoning lonestar')
        return -1

    classification = network.classify(image_data)
    logging.info("classification: (%s)", classification)
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
@app.route('/api/category', methods=['GET'])
def make_api_categorymap_public():
    if request.headers['API-ACCESS-KEY'] != CONFIG.API_ACCESS_KEY:
        abort(403)
    if request.headers['API-VERSION'] != CONFIG.API_VERSION:
        abort(400)

    return make_response(jsonify({'category_map': server_category_map}), 200)


###############################################################################
# Endpoint which provides classification of image data.
###############################################################################
@app.route('/api/classify', methods=['POST'])
def make_api_get_classify_public():
    if request.headers['API-ACCESS-KEY'] != CONFIG.API_ACCESS_KEY:
        abort(403)
    if request.headers['API-VERSION'] != CONFIG.API_VERSION:
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
    return make_response(jsonify({'version':  str(CONFIG.API_VERSION)}), 200)


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
    app.run(debug=CONFIG.FLASK_DEBUG, host=CONFIG.LISTENING_HOST, threaded=True)
