#!/bin/bash
# A new WordPress site from a host's one-click install. Run once by the WordPress container's entrypoint, with
# $WP set to the WP-CLI command. Deterministic: the same site every run.
set -euo pipefail

$WP core install --url="$WPAB_SITE_URL" --title="My WordPress Site" --admin_user=owner \
  --admin_password="{admin_password}" --admin_email=owner@mynewsite.test --skip-email
$WP option update timezone_string "Europe/London"
$WP rewrite structure '/%postname%/' --hard
$WP theme activate twentytwentyfive

# Three application passwords on the owner's account: one the owner gives the agent, one the connector uses
# (in its own container, when the setup has one), and one the checks use after the run.
$WP eval '
$user = get_user_by("id", 1);
$item = fn($name, $pw) => ["uuid" => wp_generate_uuid4(), "app_id" => "", "name" => $name, "password" => wp_fast_hash($pw),
  "created" => time(), "last_used" => null, "last_ip" => null];
update_site_option("using_application_passwords", 1); // set by WordPress when it creates the first one
update_user_meta($user->ID, "_application_passwords", [$item("Assistant", "{password}"), $item("Connector", "{connector_password}"), $item("Site monitor", "{monitor_password}")]);
'
$WP cache flush
