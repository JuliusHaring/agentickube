
FROM python:3.14


WORKDIR /code


COPY ./environments/agent-requirements.txt /code/requirements.txt


RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY code/agent/src /code/app
COPY code/shared /code/app/shared
COPY code/agent/skills/builtin /skills/builtin


CMD ["fastapi", "run", "app/main.py", "--port", "80"]