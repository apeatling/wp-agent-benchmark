# The owner's old site, for requests that move one onto WordPress: its files as the old host served them,
# at its old addresses. Static, so it's the same every run.
FROM nginx:1.27-alpine@sha256:65645c7bb6a0661892a8b03b89d0743208a18dd2f3f17a54ef4b76fb8e2f2a10
COPY default.conf /etc/nginx/conf.d/default.conf
COPY site/ /usr/share/nginx/html/
