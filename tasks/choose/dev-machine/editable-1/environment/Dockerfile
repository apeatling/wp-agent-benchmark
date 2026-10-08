# A typical developer machine, for agents whose makers don't document an environment: Node, Python and git;
# Docker (about 72% of developers use it). No PHP and no database: neither ships with macOS or Windows.
FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates curl git sudo unzip xz-utils build-essential procps ripgrep jq \
      python3 python3-pip python3-venv \
      docker.io docker-compose-v2 iptables \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Shared by every task.
RUN useradd -m -s /bin/bash dev && echo 'dev ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/dev && usermod -aG docker dev \
    && mkdir -p /app /var/lib/wpab && chown dev:dev /app
WORKDIR /app
COPY start-docker.sh /usr/local/bin/start-docker.sh
RUN chmod +x /usr/local/bin/start-docker.sh
ENTRYPOINT ["/usr/local/bin/start-docker.sh"]

# The starting files for this request.
COPY --chown=dev:dev app/ /app/
RUN touch /var/lib/wpab/started
