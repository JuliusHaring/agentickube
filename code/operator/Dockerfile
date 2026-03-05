FROM python:3.14

WORKDIR /code

# Install operator requirements (Kopf + k8s client, etc.)
COPY ./environments/operator-requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy operator source
COPY code/operator /code/operator
COPY code/shared /code/shared

# Run the Kopf operator in-cluster
CMD ["kopf", "run", "--standalone", "--all-namespaces", "operator/main.py"]
