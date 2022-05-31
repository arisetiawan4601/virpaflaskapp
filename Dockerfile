FROM python:3.8.0

WORKDIR /user/src/app

COPY "./requirements.txt" .

RUN apt-get update

RUN apt-get install ffmpeg libsm6 libxext6  -y

RUN pip install -r requirements.txt

COPY . . 

EXPOSE 5050

ENTRYPOINT [ "python", "app.py" ]