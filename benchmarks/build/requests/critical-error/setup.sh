# Yesterday afternoon someone updated the bakery's specials plugin to 1.3.0, which calls a function it doesn't
# define: every request now stops with a fatal error (front end, dashboard, REST API). WordPress caught the
# error on the login page and emailed the owner a recovery-mode link, as it does once a day.
set -euo pipefail
cp -r /opt/wpab/seed/request-files/sunnyside-specials/. wp-content/plugins/sunnyside-specials/
chown -R www-data:www-data wp-content/plugins/sunnyside-specials
# Last night: a visitor got the error, then the owner tried to log in. WordPress only emails the recovery link
# for errors on the login page or the dashboard, so that's the email the owner got.
host=${WPAB_SITE_URL#http://}
for path in / /wp-login.php; do
  code=$(curl -s -o /dev/null -w '%{http_code}' -H "Host: $host" "http://localhost$path")
  [ "$code" = 500 ] || { echo "Expected $path to fail after the update, got $code"; exit 1; }
done
for i in $(seq 1 30); do
  if curl -s -u "checks:{monitor_password}" "http://mail:8025/api/v1/search?query=to:hello@sunnysidebakery.test" | grep -q 'Your Site is Experiencing a Technical Issue'; then
    sent=1; break
  fi
  sleep 1
done
[ -n "${sent:-}" ] || { echo "WordPress didn't send the recovery-mode email"; exit 1; }
# The link in that email, fixed so the owner can forward it word for word (requests.toml): the same token and key
# every run, stored the way WordPress stores the one it emailed, and valid for the day as that one is.
$WP eval 'update_option("recovery_keys", array("wpabrecovery" => array("hashed_key" => wp_fast_hash("Kp3vQ8sLx2RmT7wN4yZ6bD"), "created_at" => time())));' --skip-plugins --skip-themes
