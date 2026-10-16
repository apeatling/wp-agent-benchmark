#!/bin/bash
# Nobody has updated the site for a while: WordPress, the theme and several plugins are a version or two
# behind, and WordPress's own update check (which the dashboard shows, and the update emails come from) knows.
set -euo pipefail
$WP core download --version=7.1.2 --force --skip-content
$WP core update-db
/opt/wpab/install.sh theme /opt/wpab/seed/request-themes.txt
/opt/wpab/install.sh plugin /opt/wpab/seed/request-plugins.txt
$WP eval '
delete_site_transient("update_core"); delete_site_transient("update_plugins"); delete_site_transient("update_themes");
wp_version_check(array(), true); wp_update_plugins(); wp_update_themes();
$core = get_site_transient("update_core"); $plugins = get_site_transient("update_plugins"); $themes = get_site_transient("update_themes");
$offer = $core && ! empty($core->updates) ? $core->updates[0] : null;
if (! $offer || "upgrade" !== $offer->response) { WP_CLI::error("WordPress doesn’t see the core update"); }
if (count((array) ($plugins->response ?? array())) < 7) { WP_CLI::error("WordPress sees only " . count((array) ($plugins->response ?? array())) . " plugin updates"); }
if (empty($themes->response["astra"])) { WP_CLI::error("WordPress doesn’t see the Astra update"); }
WP_CLI::log("Updates waiting: WordPress " . $offer->current . ", " . implode(", ", array_keys((array) $plugins->response)) . ", astra");
'
