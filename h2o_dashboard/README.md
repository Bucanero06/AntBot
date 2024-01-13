# Wave app deployment behind Nginx reverse proxy

This repo shows how to serve [Wave apps](https://wave.h2o.ai/) behind a reverse proxy.

## Prerequisites

* docker <https://www.docker.com/>
* docker compose <https://docs.docker.com/compose/>

## Running the app yourself

```sh
docker compose up
```

Once started, the app should be running at <http://localhost:80>

## Without docker

It's possible to run Nginx directly on your machine. See `nginx.conf` and `site.conf` configuration files.
