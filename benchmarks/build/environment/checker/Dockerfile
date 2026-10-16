# The checks, beside the site and out of the agent's reach: run between turns (wpab.agents.SiteOwner) and once the
# agent's sandbox has been stopped (task.toml, [[verifier.collect]]). checks.py and site.json, with the checks' login,
# are added when tasks are built and are never copied into the agent's sandbox.
FROM python:3.12-slim@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1
COPY checks.py site.json /checks/
RUN chmod 700 /checks
ENV WPAB_CHECKS_OUT=/var/log/wpab/checks
CMD ["sleep", "infinity"]
