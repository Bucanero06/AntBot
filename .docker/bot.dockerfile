# Base image
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.10

# Update and Upgrade the base image
RUN apt-get update && apt-get upgrade -y && apt-get clean

# Install Poetry
RUN pip install poetry

# Copy Poetry configuration files
COPY pyproject.toml  /app/

# Install dependencies using Poetry
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Copy application code
COPY . /app


## Set the entrypoint to run the app with Gunicorn
#ENTRYPOINT /usr/local/bin/gunicorn \
#    -b $HOST:$PORT \
#    -w $N_WORKERS \
#    -k uvicorn.workers.UvicornWorker $MODULE_PATH:$MODULE_NAME \
#    --chdir /app

# Set the entrypoint to run the app with Uvicorn
ENTRYPOINT /usr/local/bin/uvicorn \
    --host $HOST \
    --port $PORT \
    --workers $N_WORKERS \
    --reload \
    $MODULE_PATH:$MODULE_NAME

# Expose the port specified by the PORT environment variable
EXPOSE $PORT
