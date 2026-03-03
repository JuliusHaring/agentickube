
FROM python:3.14


WORKDIR /code


COPY ./environments/agent-requirements.txt /code/requirements.txt


RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt


COPY pkg/agent/src /code/app


CMD ["fastapi", "run", "app/main.py", "--port", "80"]