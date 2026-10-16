# A connector, as the agent reaches it: the site's MCP endpoint, with the connector's login added on the way
# through. The login lives only here, so the agent's sandbox has no password for the site; the
# connector is its only way in. Only the MCP endpoint is forwarded.
FROM nginx:1.27-alpine@sha256:65645c7bb6a0661892a8b03b89d0743208a18dd2f3f17a54ef4b76fb8e2f2a10
COPY default.conf /etc/nginx/conf.d/default.conf
COPY wpab-value.sh /docker-entrypoint.d/10-wpab-value.sh
RUN chmod +x /docker-entrypoint.d/10-wpab-value.sh
