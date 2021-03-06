import os, sys, dlib, random
import numpy as np
import cv2
import base64
import time
import face_recognition
from config import configDict
from sklearn.cluster import DBSCAN
from collections import defaultdict, Counter
from scipy.misc import imresize


class FaceDetector(object):
    def __init__(self):
        self.detector = dlib.get_frontal_face_detector()

    def detect(self, frame):
        try:
            return self.detector(frame, 1)
        except RuntimeError:
            return []


class FacePredictor(object):
    def __init__(self, predictor_model):
        self.predictor = dlib.shape_predictor(predictor_model)

    def predict(self, img, detection):
        return self.predictor(img, detection)


class FaceDescriptor(object):
    def __init__(self, descriptor_model):
        self.descriptor = dlib.face_recognition_model_v1(descriptor_model)

    def describe(self, img, shape):
        return self.descriptor.compute_face_descriptor(img, shape, num_jitters=1)


class Cluster(object):
    def __init__(self, thresh):
        self.cluster = DBSCAN(eps=thresh, n_jobs=1)

    def fit(self, X):
        self.cluster.fit(X)

    def get_labels(self):
        return np.asarray(self.cluster.labels_)


class VideoReader(object):
    def __init__(self, videofilepath, names_list, encodings_list):
        self.detector = FaceDetector()
        self.predictor = FacePredictor(configDict["FacePredictorPath"])
        self.descriptor = FaceDescriptor(configDict["FaceDescriptorPath"])
        self.cluster = Cluster(thresh=0.5)

        self.video = cv2.VideoCapture(videofilepath)
        self.fps = self.video.get(cv2.CAP_PROP_FPS)
        self.read_interval = round(self.fps / 2)
        self.read_cnt = 0
        self.frame_cnt = self.video.get(cv2.CAP_PROP_FRAME_COUNT)
        self.frame_height = self.video.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.frame_width = self.video.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.faces_description = []
        self.faces = []

        self.done = False

        self.cluster_result = open(configDict["UnknownImagePath"], 'rb').read()
        self.infos = {}

        self.names_list = names_list
        self.encodings_list = encodings_list
        self.names_len = len(self.names_list)

    def __del__(self):
        self.video.release()

    def get_frame(self):
        success, frame = self.video.read()
        if not success:
            self.done = True
            return None
        self.read_cnt += success
        if not self.read_cnt % self.read_interval:
            detected_faces = self.detector.detect(frame)
            for face in detected_faces:
                x0, y0, x1, y1 = face.left(), face.top(), face.right(), face.bottom()
                if any(map(lambda x: x < 0 or x > self.frame_width, [x0, x1])) or \
                        any(map(lambda y: y < 0 or y > self.frame_height, [y0, y1])):
                    continue
                crop_face = frame[y0:y1, x0:x1]
                self.faces.append(crop_face)

                shape = self.predictor.predict(frame, face)
                description = self.descriptor.describe(frame, shape)
                self.faces_description.append(description)

        ret, jpeg = cv2.imencode('.jpg', frame)
        self.jpeg = jpeg.tobytes()
        return jpeg.tobytes()

    def get_clusters(self):
        self.get_frame()
        width = 80
        height = 80
        num = 7
        font = cv2.FONT_HERSHEY_DUPLEX
        # self.infos["progress"] = self.read_cnt / self.frame_cnt

        if self.done:
            return None

        # if not self.read_cnt % 100:
        #     self.cluster_result = self.jpeg

        print('read_cnt is {0}, faces_description is {1}, total_cnt is {2}'.format(self.read_cnt, len(self.faces_description), self.frame_cnt))
        if (not self.read_cnt % 30 or self.read_cnt == self.frame_cnt) and len(self.faces_description) > num:
            faces_description = np.asarray(self.faces_description)
            self.cluster.fit(faces_description)
            counter = Counter(self.cluster.get_labels())
            total = len(self.cluster.get_labels())

            clusters = []
            infos = {}
            infos["clusters"] = {}

            labels = defaultdict(list)
            for i, l in enumerate(self.cluster.get_labels()):
                labels[l].append(i)

            for k, v in labels.items():
                name = ''

                if self.read_cnt == self.frame_cnt:
                    name = 'Unknown'
                    for index in range(self.names_len):
                        if name != 'Unknown' or k == -1:
                            break
                        current_min_distance = 999
                        for vindex in v:
                            distance_list = face_recognition.face_distance(self.encodings_list, faces_description[vindex])
                            if min(distance_list) <= 0.5 and min(distance_list) < current_min_distance:
                                current_min_distance = min(distance_list)
                                min_index = distance_list.tolist().index(min(distance_list))
                                name = self.names_list[min_index]


                img = np.ones((height, (width + 10) * num, 3), np.uint8) * 255
                indics = v[:]
                random.shuffle(indics)
                indics = indics[:num]
                original_faces = [self.faces[i] for i in indics]
                faces = [imresize(f, (width, height)) for f in original_faces]
                for j, f in enumerate(faces):
                    img[0:height, (width + 10) * j:(width + 10) * j + width, :] = f
                    # img[30:30+height, (width+10)*j:(width+10)*j+width, :] = f
                # cv2.putText(img, 'Cluster: {0} Frequency: {1:.2f}%'.format(k, counter[k] * 100.0 / total), (6, 25), font, 1.0, (0, 0, 0), 2)
                # infos.append('Cluster: {0} Frequency: {1:.2f}%'.format(k, counter[k] * 100.0 / total))
                ret, tmpimg = cv2.imencode('.jpg', img)
                infos["clusters"][str(k)] = {
                    "image": str(base64.b64encode(tmpimg))[2:-1],
                    "frequency": counter[k] * 100.0 / total,
                    "name": name
                }
                clusters.append(img)


            whole = np.concatenate(tuple(clusters))
            ret, whole = cv2.imencode('.jpg', whole)
            self.cluster_result = whole.tobytes()
            self.infos = infos

        self.infos["progress"] = int(self.read_cnt / self.frame_cnt * 100)
        self.infos["time_stamp"] = time.time()
        return self.infos
        # return {
        #     "cluster_result": self.cluster_result,
        #     "infos": self.infos
        # }
        # return self.cluster_result

if __name__ == '__main__':
    pass
