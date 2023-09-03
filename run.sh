#!/usr/bin/bash

export GIT_VERSION=$(git describe --tags)
docker compose up -d --build
