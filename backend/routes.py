from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
#from bson.objectid import ObjectId
from flask import Response
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################

@app.route('/health', methods=['GET'])
def health():
    """ Check the status of the service """
    return jsonify(status=200, message='Healthy')

@app.route('/count', methods=['GET'])
def get_count():
    """ Return the number of songs """
    return jsonify(status=200, count=db.songs.count_documents({}))

@app.route('/song', methods=['GET'])
def get_songs():
    """ Return all the songs """
    songs = parse_json(db.songs.find())
    return Response(json.dumps({"songs": songs}), status=200, mimetype='application/json')

@app.route('/song/<int:id>', methods=['GET'])
def get_song_by_id(id):
    """ Return a song by its id """
    song = db.songs.find_one({"id": id})
    if song is None:
        return jsonify({"message": "song with id not found"}), 404
    else:
        return Response(json.dumps(parse_json(song)), status=200, mimetype='application/json')

@app.route('/song/<int:id>', methods=['POST'])
def create_song(id):
    """ Create a new song """
    song = request.get_json()
    if db.songs.find_one({"id": id}):
        return jsonify({"Message": f"song with id {id} already present"}), 302
    else:
        db.songs.insert_one(song)
        return jsonify({"Message": f"song with id {id} created successfully"}), 200
    
@app.route('/song/<int:id>', methods=['PUT'])
def update_song(id):
    """ Update an existing song """
    song_data = request.get_json()

    song = db.songs.find_one({"id": id})
    if song is None:
        return jsonify({"message": "song not found"}), 404
    else:
        if song_data['title'] == song['title'] and song_data['lyrics'] == song['lyrics']:
            return jsonify({"message": "song found, but nothing updated"}), 200
        else:
            db.songs.update_one({"id": id}, {"$set": song_data})
            return jsonify({"message": f"song with id {id} updated successfully"}), 200

@app.route('/song/<int:id>', methods=['DELETE'])
def delete_song(id):
    """ Delete a song by its id """
    result = db.songs.delete_one({"id": id})

    if result.deleted_count == 0:
        return jsonify({"message": "song not found"}), 404
    else:
        return '', 204