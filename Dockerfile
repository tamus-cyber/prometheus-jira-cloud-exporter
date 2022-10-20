FROM python:3.8

WORKDIR /app

COPY ./requirements.txt ./requirements.txt
COPY ./classes ./classes
COPY main.py ./entrypoint.py
RUN python3 -m pip install -r ./requirements.txt

CMD ["python3", "entrypoint.py"]
