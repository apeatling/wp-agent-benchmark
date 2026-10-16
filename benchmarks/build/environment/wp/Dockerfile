# The WordPress site the agent works on, in its own container beside the agent's sandbox. The agent reaches
# it over the network only, like a hosted site. Official images, pinned. Nothing here is specific to one
# request: the fixture supplies seed/seed.sh (run once, with WP-CLI), seed/plugins.txt and seed/themes.txt;
# a setup may add seed/setup.sh and plugins; a request may add seed/request.sh and seed/request-plugins.txt.
FROM wordpress:cli-php8.3@sha256:36243da432a0f0a3b56dc3240ecee9b159108d71305e7c064d987a20a465bfde AS cli
FROM wordpress:7.1.3-php8.3-apache@sha256:8ecd8d8e374167ea22235acf30f80d1165b82f07ffa5bcef90c1cad8f7be251f
COPY --from=cli /usr/local/bin/wp /usr/local/bin/wp
COPY php.ini /usr/local/etc/php/conf.d/wpab.ini
COPY seed/ /opt/wpab/seed/
COPY mu-plugins/ /opt/wpab/mu-plugins/
COPY install.sh /opt/wpab/install.sh
# Plugins and themes the site needs, downloaded from wordpress.org at the pinned versions in the lists
# ("<slug> <version> [inactive]" per line), so seeding doesn't depend on the network.
COPY download.sh /opt/wpab/download.sh
RUN bash /opt/wpab/download.sh
COPY entrypoint.sh /usr/local/bin/wpab-entrypoint.sh
RUN chmod +x /usr/local/bin/wpab-entrypoint.sh /opt/wpab/seed/*.sh /opt/wpab/install.sh
ENTRYPOINT ["wpab-entrypoint.sh"]
CMD ["apache2-foreground"]
# Healthy once the seed has finished, so the agent starts on a complete site.
HEALTHCHECK --interval=3s --timeout=3s --start-period=10s --retries=200 CMD test -f /var/run/wpab-ready
