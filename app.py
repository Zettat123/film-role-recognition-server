from flask_socketio import SocketIO
from flask import Flask, request
from camera import VideoReader
from config import configDict
from flask_cors import *
from queue import Queue
import json
import copy
import threading
import time

defaultvideo = configDict["DefaultVideoPaths"]

event = threading.Event()

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
        if "progress" in info and info["progress"] == 100:
            print('COMPLETED TOO')
            break
        socketio.sleep(0.2)


def play_video(video, que):
    oldinfo = {
        "time_stamp": time.time()
    }
    while True:
        newinfo = video.get_clusters()
        if "progress" in newinfo and newinfo["progress"] == 100:
            print("COMPLETED")
            que.put(newinfo)
            break
        if newinfo["time_stamp"] - oldinfo["time_stamp"] >= 0.5:
            oldinfo = copy.deepcopy(newinfo)
            que.put_nowait(oldinfo)
            socketio.sleep(0.1)


@socketio.on('connect')
def handle_connect():
    print('Connected')


@socketio.on('select_video')
def handle_select_video(message):
    print(message)
    video = VideoReader(defaultvideo["George_Clooney"])
    q = Queue()
    socketio.start_background_task(play_video, video, q)
    socketio.start_background_task(emit_video_info, q)


@socketio.on('disconnect')
def handle_disconnect():
    print('disconnected')


CORS(app, supports_credentials=True)
if __name__ == '__main__':
    socketio.run(app, debug=True)
