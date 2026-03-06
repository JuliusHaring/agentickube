
FROM python:3.14


WORKDIR /code


COPY ./environments/agent-requirements.txt /code/requirements.txt
COPY ./environments/shared-requirements.txt /code/shared-requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY code/agent/src /code/app
COPY code/shared /code/app/shared
# Repo workspace template; agent startup syncs this into the mounted /workspace.
COPY code/agent/workspace /code/workspace

RUN rm /code/workspace/.gitignore

ENV PYTHONPATH=/code:/code/app

CMD ["gunicorn", "app.main:app", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:80", "--workers", "1", "--access-logfile", "-", "--error-logfile", "-"]