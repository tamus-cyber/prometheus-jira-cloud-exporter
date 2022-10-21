FROM python:3.8

WORKDIR /app

COPY ./requirements.txt ./requirements.txt
COPY ./main.py ./main.py
COPY ./issue_collector.py ./issue_collector.py
COPY ./custom_field_map.json ./custom_field_map.json
RUN python3 -m pip install -r ./requirements.txt

CMD ["python3", "main.py"]
