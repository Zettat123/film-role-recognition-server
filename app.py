from flask_socketio import SocketIO, send, emit, join_room, leave_room
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
import os

defaultvideo = configDict["DefaultVideoPaths"]
UPLOAD_FOLDER = configDict["FileSavePath"]
names_list, encodings_list = read_dat()

def decode_data(data):
    return json.loads(data.decode('utf-8'))


def compare_dict(dict1, dict2):
    return str(dict1) == str(dict2)


app = Flask(__name__)
socketio = SocketIO(app)


def emit_video_info(que, session_id):
    while True:
        info = que.get()
        socketio.emit('receive_cluster', {"data": info}, room=session_id)
        print('In emit, sid is {0}'.format(session_id))
        if info["progress"] == 100:
            print('COMPLETED TOO')
            break
        socketio.sleep(0.2)


def play_video(video, que, mode="select", file_path=""):
    oldinfo = {
        "time_stamp": time.time(),
        "progress": 0
    }
    while True:
        newinfo = video.get_clusters()
        if newinfo["progress"] == 100:
            print("COMPLETED")
            que.put(newinfo)
            if mode == "upload":
                video.__del__()
                try:
                    os.remove(file_path)
                except FileNotFoundError:
                    pass
            break
        if newinfo["time_stamp"] - oldinfo["time_stamp"] >= 0.5 and newinfo["progress"] != oldinfo["progress"]:
            oldinfo = copy.deepcopy(newinfo)
            que.put_nowait(oldinfo)
            socketio.sleep(0.1)


@socketio.on('connect')
def handle_connect():
    session_id = request.sid
    print('{0} Connected'.format(session_id))


@socketio.on('select_video')
def handle_select_video(message):
    print(message)
    session_id = request.sid
    video = VideoReader(defaultvideo[message], names_list, encodings_list)
    q = Queue()
    socketio.start_background_task(play_video, video, q, mode="select")
    socketio.start_background_task(emit_video_info, q, session_id)

@socketio.on('upload_video')
def handle_upload_video(data):
    session_id = request.sid
    file_path = UPLOAD_FOLDER + '\\' + secure_filename(data["fileName"]) + "." + data["fileExtensionName"]
    print('Start saving file: ' + file_path)
    with open(file_path, "wb+") as f:
        f.write(data["file"])
    print('Save finish')
    video = VideoReader(file_path, names_list, encodings_list)
    q = Queue()
    socketio.start_background_task(play_video, video, q, mode="upload", file_path=file_path)
    socketio.start_background_task(emit_video_info, q, session_id)


@socketio.on('disconnect')
def handle_disconnect():
    session_id = request.sid
    print('{0} Disconnected'.format(session_id))


CORS(app, supports_credentials=True)
if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0")
