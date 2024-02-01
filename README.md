# AntBot

[Screencast from 01-25-2024 10:41:13 PM.webm](https://github.com/Bucanero06/AntBot/assets/60953006/5c0a9a4f-78b1-4b5b-ab3b-13c439bb8d8b)

## Setup

Install docker

```bash
sudo snap refresh docker --channel=latest/edge # Has fixes I need
```

Clone the repo

```bash
git clone https://github.com/Bucanero06/AntBot.git
```

Make sure you have your .env file filled out and move inside the AntBot directory

```bash
cd AntBot
```

Run the docker containers in the background and build them if they don't exist

```bash
docker-compose up -d --build
```

The bot should be running now, you can check the logs with

```bash
docker-compose logs -f
```

or you can check the logs for a specific container with

```bash
docker-compose logs -f <container_name>
```

___

Version 2.2 for docker-compose is used to limit the resources used by the containers since. Despite version 3.x bringing 
the latest features, the resource management is meant to only work swarm mode and is not of use when working with
limited resources in a VM. Rather, optimize the containers to use fewer resources and limit the resources.

___

## Stack-Description

### FastAPI (OKX_REST)

The services running FastAPI applications are the `okx_rest` and `okx_websockets` services. The `okx_rest` service
is used to interact with the OKX exchange and the `okx_websockets` service is used to provide real-time data to the
Redis-Stack database.

FastAPI is a modern, fast (high performance), web framework for building APIs with Python 3.9+ based on standard Python
type hints. It is designed to be easy to use and learn, and it is also highly performant. It is built on top of
Starlette for the web parts and Pydantic for the data parts.

In addition to the RESTful API, a websocket server is used to provide real-time data from the exchange to
the Redis-Stack database. This is used to provide real-time data to the user interface and other services that
require up-to-date data.

### Uvicorn (ASGI Server)

Uvicorn is a lightning-fast ASGI server, built on uvloop and httptools. It is used to serve the FastAPI applications
and is used to handle the asynchronous requests made to the RESTful API and the websocket server.

### Gunicorn (WSGI Server)

We use Gunicorn to serve the FastAPI application in production.
Gunicorn is a Python WSGI HTTP Server for UNIX.
The difference between ASGI and WSGI is that ASGI is designed to handle asynchronous requests and WSGI is designed to
handle synchronous requests.
The reasoning of handling synchronous requests with Gunicorn is that the RESTful API is not designed to handle


### Pydantic (Data Validation)

### Nginx (Optional - Reverse Proxy)

### Redis (Cache and Message Broker)

### Asyncio (Concurrent Requests)

### Websockets (Real-time Data)

### Requests (HTTP Requests)

### Wave (Dashboard and Data Visualization)

### VectorBT(PRO) (Backtesting and Strategy Development)

### Nautilus Trader (High-Frequency Trading)

### Docker (Containerization)

### Docker-Compose (Orchestration)

### GCP Logging & Monitoring + Installed Ops Agent (Monitoring)

### Firebase (GCP) (Authentication)

### Oauth2 (Authentication)

### TradingView (Widgets and Alerts)

##


