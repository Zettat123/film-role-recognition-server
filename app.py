from flask import Flask, request
from flask_socketio import SocketIO
from camera import VideoReader
from config import configDict
from flask_cors import *
from queue import Queue
import json
import copy
import threading

defaultvideo = configDict["DefaultVideoPaths"]

event = threading.Event()

def decode_data(data):
    return json.loads(data.decode('utf-8'))


def compare_info_dict(dict1, dict2):
    return str(dict1) == str(dict2)
    # if len(dict1) != len(dict2):
    #     return False
    # keys = list(dict1.keys())
    # for key in keys:
    #     return compare_info_dict(dict1[key], dict2[key])


app = Flask(__name__)
socketio = SocketIO(app)


def ack():
    print('YHH')


def emit_info(info):
    socketio.emit('receive_info', {"data": info})


def emit_video_info(que):
    while True:
        info = que.get()
        if info == 233:
            break
        socketio.emit('receive_info', {"data": info})
        socketio.sleep(0.2)


def play_video(video, que):
    oldinfo = {}
    while True:
        newinfo = video.get_clusters()
        if newinfo is None:
            que.put(233)
            break
        if not compare_info_dict(oldinfo, newinfo):
            oldinfo = copy.deepcopy(newinfo)
            event.set()
            que.put_nowait(oldinfo)
            socketio.sleep(0.1)


@socketio.on('connect')
def handle_connect():
    print('Connected')


@socketio.on('start')
def handle_start():
    video = VideoReader(defaultvideo["George_Clooney"])
    q = Queue()
    socketio.start_background_task(play_video, video, q)
    socketio.start_background_task(emit_video_info, q)






CORS(app, supports_credentials=True)
if __name__ == '__main__':
    socketio.run(app, debug=True)
