# OpenAI's published Codex cloud image, used as-is (https://github.com/openai/codex-universal).
FROM ghcr.io/openai/codex-universal@sha256:905e512f36460e1be4cfedb30928a8a28299edb0fcd5de7998ceaa72d27fe304
# Its entrypoint sets up the language runtimes, then always opens a login shell, so it can't run the
# sandbox's command. This runs the same setup, then the command.
RUN printf '#!/bin/bash\n/opt/codex/setup_universal.sh > /var/log/codex-setup.log 2>&1\nexec "$@"\n' > /usr/local/bin/codex-start.sh \
    && chmod +x /usr/local/bin/codex-start.sh
ENTRYPOINT ["/usr/local/bin/codex-start.sh"]

# Shared by every task.
RUN mkdir -p /app /var/lib/wpab
WORKDIR /app

# The starting files for this request.
COPY app/ /app/
RUN touch /var/lib/wpab/started
