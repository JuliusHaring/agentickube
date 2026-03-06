
FROM python:3.14


WORKDIR /code


COPY ./environments/agent-requirements.txt /code/requirements.txt
COPY ./environments/shared-requirements.txt /code/shared-requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY code/agent/src /code/app
COPY code/shared /code/app/shared
COPY code/agent/workspace /workspace

RUN rm /workspace/.gitignore

ENV PYTHONPATH=/code:/code/app

CMD ["gunicorn", "app.main:app", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:80", "--workers", "1", "--access-logfile", "-", "--error-logfile", "-"]