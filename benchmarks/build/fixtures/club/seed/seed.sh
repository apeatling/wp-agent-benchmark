#!/bin/bash
# Portwen Sailing Club: a volunteer-run dinghy club's site, on WordPress since 2017, with a classic theme and
# years of news written by a few committee members. Run once by the WordPress container's entrypoint, with $WP
# set to the WP-CLI command. Deterministic: the same site every run.
set -euo pipefail
S=/opt/wpab/seed

# The owner is the club secretary, Helen, who set the site up.
$WP core install --url="$WPAB_SITE_URL" --title="Portwen Sailing Club" --admin_user=portwensc \
  --admin_password="{admin_password}" --admin_email=secretary@portwensailing.test --skip-email
$WP user update portwensc --display_name="Helen Treloar" --first_name=Helen --last_name=Treloar --user_registered="2017-02-11 18:20:00"
$WP option update blogdescription "Dinghy sailing on Portwen bay since 1968"
$WP option update timezone_string "Europe/London"
$WP option update date_format "j F Y"
$WP rewrite structure '/%postname%/' --hard

# No bundled extras or default content: the site's own plugins are below.
$WP plugin delete akismet hello || true
$WP post delete $($WP post list --post_type=post,page --format=ids) --force || true
$WP comment delete $($WP comment list --format=ids) --force || true
$WP term update category 1 --name=News --slug=news

# The committee members who write for the site.
$WP user create dave dave.pengelly@portwensailing.test --role=editor --display_name="Dave Pengelly" --first_name=Dave --last_name=Pengelly --user_registered="2017-02-11 19:02:00" --porcelain >/dev/null
$WP user create sue sue.hocking@portwensailing.test --role=editor --display_name="Sue Hocking" --first_name=Sue --last_name=Hocking --user_registered="2018-04-02 20:15:00" --porcelain >/dev/null
$WP user create tom tom.rowe@portwensailing.test --role=author --display_name="Tom Rowe" --first_name=Tom --last_name=Rowe --user_registered="2019-01-20 17:40:00" --porcelain >/dev/null

# Theme and plugins (themes.txt, plugins.txt).
/opt/wpab/install.sh theme "$S/themes.txt"
$WP theme activate astra
/opt/wpab/install.sh plugin "$S/plugins.txt"

# (LiteSpeed Cache prints "Purged all caches" on many WP-CLI commands, hence the tail -n1 on IDs.)
# Pages, in the classic editor. The contact form and the results table are made first, for their shortcodes.
form=$($WP post list --post_type=wpcf7_contact_form --format=ids | awk '{print $1}')
[ -n "$form" ] || { echo "no contact form"; exit 1; }
$WP post update "$form" --post_title="Contact form"
table=$($WP eval-file "$S/content/results.php" | tail -n1)
page() { $WP post create --post_type=page --post_status=publish --post_author=1 --post_title="$1" --post_name="$2" --post_date="$3" "$S/content/$4.html" --porcelain | tail -n1; }
home=$(page "Home" home "2017-02-11 18:40:00" home)
page "About the club" about "2017-02-11 18:45:00" about >/dev/null
page "Who's who" whos-who "2017-02-11 18:50:00" whos-who >/dev/null
page "Join us" join-us "2017-02-12 10:05:00" join >/dev/null
page "Sailing programme" sailing-programme "2017-02-12 10:20:00" programme >/dev/null
results=$(page "Results" results "2017-04-20 21:10:00" results)
contact=$(page "Contact" contact "2017-02-12 10:30:00" contact)
$WP post update "$results" --post_content="$(sed "s/{table}/$table/" "$S/content/results.html")"
$WP post update "$contact" --post_content="$(sed "s/{form}/$form/" "$S/content/contact.html")"
news=$($WP post create --post_type=page --post_status=publish --post_author=1 --post_title="News" --post_name=news --post_date="2017-02-12 10:35:00" --porcelain | tail -n1)
$WP option update show_on_front page
$WP option update page_on_front "$home"
$WP option update page_for_posts "$news"

# The news since 2017, with some comments from members.
$WP eval-file "$S/content/news.php"

# Upcoming events in The Events Calendar.
$WP eval-file "$S/content/events.php" --user=portwensc

# The menu, and the footer: the club's address and the usual small print.
menu=$($WP menu create "Main menu" --porcelain | tail -n1)
for id in $home $($WP post list --post_type=page --name=about --field=ID) $($WP post list --post_type=page --name=sailing-programme --field=ID) \
          $news $results $($WP post list --post_type=page --name=whos-who --field=ID) $($WP post list --post_type=page --name=join-us --field=ID) $contact; do
  $WP menu item add-post "$menu" "$id" >/dev/null
done
$WP menu item add-custom "$menu" "Events" "$WPAB_SITE_URL/events/" >/dev/null
$WP menu location assign "$menu" primary
$WP eval-file "$S/content/footer.php"

# Plugin settings as the club has them (content/settings.php): everything at its defaults, except that
# Wordfence's "Disable WordPress application passwords" (on by default) was turned off by the owner, who uses
# them. LiteSpeed Cache only caches pages on a LiteSpeed server, so on this Apache host it serves nothing stale.
$WP eval-file "$S/content/settings.php"

# Three application passwords on the owner's account: one the owner gives the agent, one the connector uses
# (in its own container, when the setup has one), and one the checks use after the run. Fixed values, so the request and the checks can name them.
$WP eval '
$user = get_user_by("login", "portwensc");
$item = fn($name, $pw) => ["uuid" => wp_generate_uuid4(), "app_id" => "", "name" => $name, "password" => wp_fast_hash($pw),
  "created" => time(), "last_used" => null, "last_ip" => null];
update_site_option("using_application_passwords", 1); // set by WordPress when it creates the first one
update_user_meta($user->ID, "_application_passwords", [$item("Assistant", "{password}"), $item("Connector", "{connector_password}"), $item("Site monitor", "{monitor_password}")]);
'
$WP cache flush
