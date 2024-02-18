FROM python:3.10

WORKDIR /app

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

EXPOSE 10101
CMD ["wave", "run", "h2o_dashboard.dashboard", "--no-reload"]



