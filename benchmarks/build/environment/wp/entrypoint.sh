#!/bin/bash
# Start Apache through the image's own entrypoint (which copies WordPress in and writes wp-config.php), and
# seed the site in the background once the database answers. The healthcheck waits for /var/run/wpab-ready.
set -e

seed() {
  until [ -f /var/www/html/wp-config.php ] && php -r '
      $c = @new mysqli(getenv("WORDPRESS_DB_HOST"), getenv("WORDPRESS_DB_USER"), getenv("WORDPRESS_DB_PASSWORD"), getenv("WORDPRESS_DB_NAME"));
      exit($c->connect_errno ? 1 : 0);' 2>/dev/null; do
    sleep 1
  done
  cd /var/www/html
  mkdir -p wp-content/mu-plugins && cp /opt/wpab/mu-plugins/*.php wp-content/mu-plugins/
  # WP-CLI gets what a typical host gives it: plenty of memory for shop plugins.
  export WP_CLI_PHP_ARGS="-d memory_limit=512M"
  export WP="wp --allow-root --path=/var/www/html"
  # Each step fails loudly: a site that isn't seeded as written stays unready, so the run stops.
  /opt/wpab/seed/seed.sh || { echo "Seed failed"; exit 1; }
  # Then the setup's own steps (benchmarks/build/setups.toml), if it has any.
  if [ -f /opt/wpab/seed/setup.sh ]; then
    mkdir -p /run/wpab-connector
    bash /opt/wpab/seed/setup.sh || { echo "Setup failed"; exit 1; }
  fi
  # Then the request's: what the owner's situation is when they ask (benchmarks/build/requests/<id>/setup.sh).
  if [ -f /opt/wpab/seed/request.sh ]; then
    bash /opt/wpab/seed/request.sh || { echo "Request setup failed"; exit 1; }
  fi
  $WP cache flush || true
  # The site as the agent finds it, for the checks to compare against (mu-plugins/wpab-monitor.php).
  mkdir -p /var/lib/wpab
  $WP eval 'echo wp_json_encode( wpab_state() );' --skip-plugins --skip-themes > /var/lib/wpab/baseline.json
  # Files belong to the web server, as on a host, so WordPress can update plugins itself.
  chown -R www-data:www-data /var/www/html /var/lib/wpab
  mkdir -p /var/log/wpab && chown www-data:www-data /var/log/wpab  # the activity log (mu-plugins/wpab-activity.php)
  touch /var/run/wpab-ready
}

seed > /var/log/wpab-seed.log 2>&1 &
exec docker-entrypoint.sh "$@"
