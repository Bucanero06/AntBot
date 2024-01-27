[Screencast from 01-25-2024 10:41:13 PM.webm](https://github.com/Bucanero06/AntBot/assets/60953006/5c0a9a4f-78b1-4b5b-ab3b-13c439bb8d8b)


# Setup

Install docker
```bash
sudo snap refresh docker --channel=latest/edge # Has bug fixes i need
```

Clone the repo
```bash
git clone https://github.com/Bucanero06/AntBot.git
```

Make sure you have your .env file filled out and moved inside the AntBot folder

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

