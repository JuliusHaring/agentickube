FROM python:3.14

WORKDIR /code

# Install operator requirements (Kopf + k8s client, etc.)
COPY ./environments/operator-requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy operator source
COPY code/operator /code/operator
COPY code/shared /code/shared
RUN chmod +x /code/operator/entrypoint.sh

# WATCH_NAMESPACE: set to a namespace name to watch only that namespace; unset = all-namespaces.
ENTRYPOINT ["/code/operator/entrypoint.sh"]
CMD []
