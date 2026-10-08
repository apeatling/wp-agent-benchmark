# Claude Code's documented cloud environment (https://code.claude.com/docs/en/cloud-environments):
# Ubuntu 24.04; Node 22; Python 3; PHP 8.3 and Composer; Ruby; Java 21; Go; Rust; PostgreSQL 16 and Redis
# installed but not running; Docker.
FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates curl git sudo unzip xz-utils build-essential procps ripgrep jq \
      python3 python3-pip python3-venv \
      php8.3-cli php8.3-common php8.3-curl php8.3-mbstring php8.3-xml php8.3-zip php8.3-gd php8.3-sqlite3 php8.3-pgsql php8.3-mysql composer \
      ruby-full openjdk-21-jdk-headless golang-go rustc cargo \
      postgresql-16 redis-server \
      docker.io docker-compose-v2 iptables \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*
