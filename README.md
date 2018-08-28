# Film-Role-Recognition Server

## 依赖
系统用 python 3 语法编写，依赖的库有：
- OpenCV(需要本地编译版，不能用包管理器下载的版本，因为需要用到VideoCapture这个函数)
- numpy
- scikit-learn
- scipy
- dlib(需要本地编译版本)
- flask

## 测试视频
默认有 3 个测试用视频，分别为：
1. George_Clooney.mp4
2. Ewan_McGregor.mp4
3. Tom_Hanks.mp4

若需增删测试视频，需修改下方的 `config.py` 文件，前端需同步修改


## config.py
运行/部署前需先修改 `config.py` 文件, 文件内容如下:
```
configDict = {
    "facescrubPath": 人脸图片数据路径,
    "FacePredictorPath": ./model/shape_predictor_68_face_landmarks.dat 文件路径,
    "FaceDescriptorPath": ./model/dlib_face_recognition_resnet_model_v1.dat 文件路径,
    "UnknownImagePath": unknown.jpg 文件路径,
    "FileSavePath": 上传的视频暂存目录,
    "DefaultVideoPaths": {
        'George_Clooney': George_Clooney.mp4 文件路径,
        'Ewan_McGregor': Ewan_McGregor.mp4 文件路径,
        'Tom_Hanks': Tom_Hanks.mp4 文件路径,
    }
}
```
若相对路径无法使用，应改为绝对路径

## 预读人脸数据
- 本应用采用 [face_recognition](https://github.com/ageitgey/face_recognition) 进行人脸识别。为提高效率，应使用 `read_image_one_face.py` 提前将人脸数据保存至 `encodings_one.dat` 和 `names_one.dat` 中。
- 目前 `.dat` 文件中已保存来自 http://vintage.winklerbros.net/facescrub.html 的明星人脸数据。
- `read_image_one_face.py` 读取的文件路径为 `[facescrubPath]/[ACTOR_NAME]/[图片文件]`。