from flask_socketio import SocketIO
from flask import Flask, request
from camera import VideoReader
from config import configDict
from flask_cors import *
from queue import Queue
from werkzeug import secure_filename
from read_dat_one_face import read_dat
import json
import copy
import time

defaultvideo = configDict["DefaultVideoPaths"]
UPLOAD_FOLDER = configDict["FileSavePath"]
names_list, encodings_list = read_dat()

def decode_data(data):
    return json.loads(data.decode('utf-8'))


def compare_dict(dict1, dict2):
    return str(dict1) == str(dict2)


app = Flask(__name__)
socketio = SocketIO(app)


def emit_info(info):
    socketio.emit('receive_info', {"data": info})


def emit_video_info(que):
    while True:
        info = que.get()
        socketio.emit('receive_cluster', {"data": info})
        if info["progress"] == 100:
            print('COMPLETED TOO')
            break
        socketio.sleep(0.2)


def play_video(video, que):
    oldinfo = {
        "time_stamp": time.time(),
        "progress": 0
    }
    while True:
        newinfo = video.get_clusters()
        if newinfo["progress"] == 100:
            print("COMPLETED")
            que.put(newinfo)
            break
        if newinfo["time_stamp"] - oldinfo["time_stamp"] >= 0.5 and newinfo["progress"] != oldinfo["progress"]:
            oldinfo = copy.deepcopy(newinfo)
            que.put_nowait(oldinfo)
            socketio.sleep(0.1)


@socketio.on('connect')
def handle_connect():
    print('Connected')


@socketio.on('select_video')
def handle_select_video(message):
    print(message)
    video = VideoReader(defaultvideo[message], names_list, encodings_list)
    q = Queue()
    socketio.start_background_task(play_video, video, q)
    socketio.start_background_task(emit_video_info, q)

@socketio.on('upload_video')
def handle_upload_video(data):
    file_path = UPLOAD_FOLDER + '\\' + secure_filename(data["fileName"]) + "." + data["fileExtensionName"]
    print('Start uploading file: ' + file_path)
    with open(file_path, "wb+") as f:
        f.write(data["file"])
    print('Upload finish')
    video = VideoReader(file_path, names_list, encodings_list)
    q = Queue()
    socketio.start_background_task(play_video, video, q)
    socketio.start_background_task(emit_video_info, q)


@socketio.on('disconnect')
def handle_disconnect():
    print('Disconnected')


CORS(app, supports_credentials=True)
if __name__ == '__main__':
    socketio.run(app, debug=True)
