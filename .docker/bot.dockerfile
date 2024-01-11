FROM tiangolo/uvicorn-gunicorn-fastapi:python3.10

# Update and Upgrade the base image
RUN apt-get update && apt-get upgrade -y && apt-get clean

# Copy requirements and install dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY . /app

# Use environment variables to control the startup behavior
ENV MODULE_NAME=main
ENV VARIABLE_NAME=app
ENV PORT=8080

# Set the entrypoint to run the app with Gunicorn
ENTRYPOINT /usr/local/bin/gunicorn \
    -b 0.0.0.0:$PORT \
    -w 4 \
    -k uvicorn.workers.UvicornWorker $MODULE_NAME:$VARIABLE_NAME \
    --chdir /app

# Expose the port specified by the PORT environment variable
EXPOSE $PORT
