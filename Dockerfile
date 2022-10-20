FROM python:3.8

WORKDIR /app

RUN python3 -m pip install prometheus_client jira

COPY ./classes ./classes

COPY main.py ./entrypoint.py

CMD ["python3", "entrypoint.py"]
