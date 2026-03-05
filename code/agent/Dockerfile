
FROM python:3.14


WORKDIR /code


COPY ./environments/agent-requirements.txt /code/requirements.txt
COPY ./environments/shared-requirements.txt /code/shared-requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY code/agent/src /code/app
COPY code/shared /code/app/shared
COPY code/agent/workspace /code/app/workspace

RUN rm /code/app/workspace/.gitignore

ENV PYTHONPATH=/code

CMD ["fastapi", "run", "app/main.py", "--port", "80"]