import face_recognition
import os
from config import configDict

FACESCRUB_PATH = configDict["facescrubPath"]

names_file = open("names_one.dat", "w+", encoding="utf-8")
encodings_file = open("encodings_one.dat", "w+", encoding="utf-8")

count = 0
names = []
encodings = []

folders = os.listdir(FACESCRUB_PATH)

for folder in folders:
    # if count >= 3:
    #     break
    names_file.write(folder + "\n")

    face_dir = FACESCRUB_PATH + "\\" + folder + "\\" + "face"
    face_files = os.listdir(face_dir)
    current_encodings = []

    for face_file in face_files:
        img_path = face_dir + "\\" + face_file
        try:
            current_image = face_recognition.load_image_file(img_path)
        except OSError:
            print("File read failed:" + img_path)
            continue
        current_encoding = face_recognition.face_encodings(current_image)
        if len(current_encoding) == 0:
            continue
        current_encodings.append(current_encoding[0])

    current_encodings_len = len(current_encodings)
    best_face_distance = current_encodings_len
    best_face_index = 0
    for index in range(current_encodings_len):
        temp_distance = sum(face_recognition.face_distance(current_encodings, current_encodings[index]))
        if temp_distance < best_face_distance:
            best_face_distance = temp_distance
            best_face_index = index

    encodings_file.write(str(current_encodings[best_face_index].tolist()) + "\n")

    print(count)
    count += 1

names_file.close()
encodings_file.close()

