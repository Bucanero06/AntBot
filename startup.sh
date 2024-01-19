#!/bin/bash

## Set up a startup script
## chmod +x startup.sh
## sudo systemctl enable startup.sh
## sudo systemctl start startup.sh
## sudo systemctl status startup.sh
## docker-compose ps



# Update package lists and install Docker and Docker Compose
sudo apt update
#sudo apt install -y docker.io docker-compose

sudo apt install snapd # Install snap or assure it is installed
# Install docker
sudo snap refresh docker --channel=latest/edge # Has bug fixes i need

# Wait for the network to be up
until ping -c 1 -W 1 google.com >/dev/null 2>&1; do
  >&2 echo "Network not yet up, waiting..."
  sleep 1
done


# Run docker-compose up
docker-compose up -d

# Check if all services are running
for service in $(docker-compose ps -q); do
  if ! docker inspect --format '{{.State.Status}}' $service | grep -q running; then
    >&2 echo "Service $service is not running, exiting..."
    exit 1
  fi
done

>&2 echo "All services are up and running."

# Configure the Google Cloud firewall
gcloud compute firewall-rules create docker-compose-allow-all \
  --allow tcp:80 \
  --source-ranges 0.0.0.0/0 \
  --target-tags docker-compose

# Obtain the VPS's public IP address
VPS_IP=$(curl -s https://api.ipify.org)

# Print the VPS's public IP address and mapped port
echo "Your service is accessible at: http://$VPS_IP"