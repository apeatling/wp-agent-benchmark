#!/bin/bash
# Harbour Plumbing and Heating: a two-van plumbing business's site, built with Elementor by a freelancer a few
# years ago and looked after by the owner since. Run once by the WordPress container's entrypoint, with $WP set
# to the WP-CLI command. Deterministic: the same site every run.
set -euo pipefail
S=/opt/wpab/seed

$WP core install --url="$WPAB_SITE_URL" --title="Harbour Plumbing and Heating" --admin_user=harbourplumbing \
  --admin_password="{admin_password}" --admin_email=gareth@harbourplumbing.test --skip-email
$WP user update harbourplumbing --first_name=Gareth --last_name=Penrose --display_name="Gareth Penrose"
$WP option update blogdescription "Plumbing, heating and boiler servicing in West Cornwall"
$WP option update timezone_string "Europe/London"
$WP option update date_format "j F Y"
$WP option update default_comment_status closed
$WP rewrite structure '/%postname%/' --hard

# No bundled extras or default content.
$WP plugin delete akismet hello || true
$WP post delete $($WP post list --post_type=post,page --format=ids) --force || true

# Hello Elementor (themes.txt) and the plugins (plugins.txt).
/opt/wpab/install.sh theme "$S/themes.txt"
$WP theme activate hello-elementor
$WP theme delete twentytwentythree twentytwentyfour || true
/opt/wpab/install.sh plugin "$S/plugins.txt"

# Each plugin's first-run setup, done as the freelancer did it: wizards finished or skipped, no account
# connected (Rank Math's wizard skips registration), SSL left as it was (the site is plain http here).
$WP option update eael_setup_wizard complete
$WP option delete hfe_start_onboarding || true
$WP option update hfe_onboarding_triggered yes
$WP option update rank_math_registration_skip 1
$WP option update rank_math_wizard_completed 1
$WP option delete rsssl_redirect_to_settings_page || true
$WP option update elementor_onboarded 1
$WP option update updraft_interval weekly
$WP option update updraft_interval_database weekly
$WP option update updraft_retain 4
$WP option update updraft_retain_db 4
# WPCode's site-wide header: the Search Console verification tag the freelancer added.
$WP option update ihaf_insert_header '<meta name="google-site-verification" content="hpH-test-0c9f2e7a41b8d35" />'

# The pages, contact form, menu, header and footer, built through Elementor (content/site.php).
$WP eval-file "$S/content/site.php" --user=harbourplumbing

# Three application passwords on the owner's account: one the owner gives the agent, one the connector uses
# (in its own container, when the setup has one), and one the checks use after the run. Fixed values, so the request and the checks can name them.
$WP eval '
$user = get_user_by("login", "harbourplumbing");
$item = fn($name, $pw) => ["uuid" => wp_generate_uuid4(), "app_id" => "", "name" => $name, "password" => wp_fast_hash($pw),
  "created" => time(), "last_used" => null, "last_ip" => null];
update_site_option("using_application_passwords", 1); // set by WordPress when it creates the first one
update_user_meta($user->ID, "_application_passwords", [$item("Assistant", "{password}"), $item("Connector", "{connector_password}"), $item("Site monitor", "{monitor_password}")]);
'
$WP cache flush
