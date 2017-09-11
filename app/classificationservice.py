#!flask/bin/python
from lib import dicebox_config as config
from flask import Flask, jsonify, request, make_response, abort
from flask_cors import CORS, cross_origin
import base64
from lib.network import Network
import logging
import json

# Setup logging.
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p',
    level=logging.DEBUG,
    filemode='w',
    filename="%s/classificationservice.log" % config.LOGS_DIR
)

network = Network(config.NN_PARAM_CHOICES)

with open('./category_map.json') as data_file:
    jdata = json.load(data_file)
server_category_map = {}
for d in jdata:
    server_category_map[str(jdata[d])] = str(d)


def get_classification(image_data):
    try:
        network.create_lonestar(create_model=True,
                                weights_filename="%s/%s" % (config.WEIGHTS_DIR, config.MODEL_WEIGHTS_FILENAME))
    except:
        logging.error('Error summoning lonestar')
        return -1

    try:
        classification = network.classify('dicebox_raw', image_data)
        logging.info("classification: (%s)" % classification)
        return classification[0]

    except:
        logging.error('Error making prediction..')
        return -1


app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "http://localhost:*"}})

@app.route('/api/categories', methods=['GET'])
def make_api_categorymap_public():
    if request.headers['API-ACCESS-KEY'] != config.API_ACCESS_KEY:
        abort(401)
    if request.headers['API-VERSION'] != config.API_VERSION:
        abort(400)

    return make_response(jsonify({'category_map': server_category_map}), 201)


@app.route('/api/classify', methods=['POST'])
def make_api_get_classify_public():
    if request.headers['API-ACCESS-KEY'] != config.API_ACCESS_KEY:
        abort(401)
    if request.headers['API-VERSION'] != config.API_VERSION:
        abort(400)
    if not request.json:
        abort(400)
    if 'data' in request.json and type(request.json['data']) != unicode:
        abort(400)

    encoded_image_data = request.json.get('data')
    decoded_image_data = base64.b64decode(encoded_image_data)
    classification = get_classification(decoded_image_data)

    return make_response(jsonify({'classification': classification}), 201)


@app.route('/api/version', methods=['GET'])
def make_api_version_public():
    return make_response(jsonify({'version':  str(config.API_VERSION)}), 201)


@app.route('/health/plain', methods=['GET'])
@cross_origin()
def make_health_plain_public():
    return make_response('true', 201)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


if __name__ == '__main__':
    logging.debug('starting flask app')
    app.run(debug=config.FLASK_DEBUG, host=config.LISTENING_HOST, threaded=True)
