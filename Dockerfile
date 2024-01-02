FROM tiangolo/uvicorn-gunicorn-fastapi:python3.10

# Update and Upgrade the base image
RUN apt update && apt upgrade -y

# Copy requirements and install dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# Copy application code
COPY ./ /app

# Set environment variables for logs
#ENV ACCESS_LOG=${ACCESS_LOG:-/proc/1/fd/1}
#ENV ERROR_LOG=${ERROR_LOG:-/proc/1/fd/2}

# Set the entrypoint to run the app with Gunicorn
ENTRYPOINT /usr/local/bin/gunicorn \
    -b 0.0.0.0:8080 \
    -w 4 \
    -k uvicorn.workers.UvicornWorker main:app \
    --chdir /app
#    --access-logfile "ACCESS_LOG" \
#    --error-logfile "ERROR_LOG"

## Expose port 80
#EXPOSE 8080
