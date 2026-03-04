
FROM python:3.14


WORKDIR /code


COPY ./environments/agent-requirements.txt /code/requirements.txt


RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY src/agent/src /code/app
COPY src/shared /code/app/shared


CMD ["fastapi", "run", "app/main.py", "--port", "80"]