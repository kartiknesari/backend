#!/bin/bash

echo "Starting Docker Compose Container \n"
docker compose --file "docker-compose.dev.yaml" up -d --build

echo "Container Created \n"