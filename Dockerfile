FROM python:3.6

RUN apt-get -y update
RUN apt-get -y install libboost-all-dev cmake
RUN pip3 install dlib

WORKDIR /app
ADD ./ /app

RUN pip install -r requirements.txt

EXPOSE 5000
CMD ["python3", "app.py"]