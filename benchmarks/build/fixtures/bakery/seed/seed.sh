#!/bin/bash
# Sunnyside Bakery: a small business site that has been running for a while. Run once by the WordPress
# container's entrypoint, with $WP set to the WP-CLI command. Deterministic: the same site every run.
set -euo pipefail
S=/opt/wpab/seed

$WP core install --url="$WPAB_SITE_URL" --title="Sunnyside Bakery" --admin_user=sunnyside \
  --admin_password="{admin_password}" --admin_email=hello@sunnysidebakery.test --skip-email
$WP option update blogdescription "Bread and cakes, baked every morning"
$WP option update timezone_string "Europe/London"
$WP option update date_format "j F Y"
$WP rewrite structure '/%postname%/' --hard
$WP theme activate twentytwentyfive

# No bundled extras or default content: the site's own plugins are below.
$WP plugin delete akismet hello || true
$WP post delete $($WP post list --post_type=post,page --format=ids) --force || true

page() { $WP post create --post_type=page --post_status=publish --post_title="$1" --post_name="$2" "$S/content/$2.html" --porcelain; }
home=$(page "Home" home)
page "Menu" menu >/dev/null
page "About us" about >/dev/null
page "Contact" contact >/dev/null
news=$($WP post create --post_type=page --post_status=publish --post_title="News" --post_name=news --porcelain)
$WP option update show_on_front page
$WP option update page_on_front "$home"
$WP option update page_for_posts "$news"

post() { $WP post create --post_status=publish --post_title="$1" --post_date="$2" "$S/content/$3.html" >/dev/null; }
post "Hot cross buns are back" "2026-03-20 08:00:00" post-buns
post "Our new sourdough starter class" "2026-06-02 09:30:00" post-class
post "Summer opening hours" "2026-07-15 07:45:00" post-summer

# Plugins (plugins.txt), and the bakery's own specials plugin, which the menu page uses.
/opt/wpab/install.sh plugin "$S/plugins.txt"
cp -r "$S/plugins/sunnyside-specials" wp-content/plugins/
$WP plugin activate sunnyside-specials
$WP option update sunnyside_specials_list '{"items":["Pear and ginger cake","Cheese and chive scones"]}' --format=json

# The shop: pounds, collection only, open (not "coming soon"), with what the bakery sells online.
$WP option update woocommerce_currency GBP
$WP option update woocommerce_default_country "GB"
$WP option update woocommerce_store_address "12 Harbour Street"
$WP option update woocommerce_store_city "Portwen"
$WP option update woocommerce_coming_soon no
$WP option update woocommerce_onboarding_profile '{"skipped":true}' --format=json
$WP option update woocommerce_cod_settings '{"enabled":"yes","title":"Pay when you collect","description":"Pay in the shop when you collect your order.","instructions":"","enable_for_methods":[],"enable_for_virtual":"yes"}' --format=json
cakes=$($WP wc product_cat create --name="Celebration cakes" --user=sunnyside --porcelain)
seasonal=$($WP wc product_cat create --name="Seasonal" --user=sunnyside --porcelain)
classes=$($WP wc product_cat create --name="Classes" --user=sunnyside --porcelain)
product() { $WP wc product create --user=sunnyside --type=simple --status=publish --name="$1" --slug="$2" --regular_price="$3" \
  --categories="[{\"id\":$4}]" --description="$5" --short_description="$6" --porcelain >/dev/null; }
product "Chocolate celebration cake" chocolate-celebration-cake 42 "$cakes" \
  "<p>Three layers of chocolate sponge with chocolate ganache. Serves 16. Order at least three days ahead.</p>" "Serves 16. Three days' notice."
product "Victoria sponge" victoria-sponge 24 "$cakes" \
  "<p>Our classic sponge with raspberry jam and vanilla buttercream. Serves 10.</p>" "Serves 10."
product "Lemon drizzle loaf" lemon-drizzle-loaf 12 "$cakes" \
  "<p>A whole lemon drizzle loaf, the same one we sell by the slice.</p>" "A whole loaf."
product "Stollen" stollen 14 "$seasonal" \
  "<p>Our Christmas stollen, with marzipan, rum-soaked fruit and plenty of icing sugar.</p>" "Christmas only."
product "Sourdough starter class" sourdough-starter-class 45 "$classes" \
  "<p>Two hours on a Saturday morning: make your own starter and take home a loaf.</p>" "Saturday mornings, two hours."

# The header menu, as the Site Editor saves it: the theme's navigation menu (made when the theme was switched
# on, listing every page), edited down to the pages visitors need.
link() { id=$($WP post list --post_type=page --name="$1" --field=ID); echo "<!-- wp:navigation-link {\"label\":\"$2\",\"type\":\"page\",\"id\":$id,\"url\":\"$WPAB_SITE_URL/$1/\",\"kind\":\"post-type\"} /-->"; }
nav=$($WP post list --post_type=wp_navigation --field=ID | head -1)
[ -n "$nav" ] || nav=$($WP post create --post_type=wp_navigation --post_status=publish --post_title=Navigation --porcelain)
$WP post update "$nav" - <<< "$(link menu Menu)$(link shop 'Order a cake')$(link about 'About us')$(link news News)$(link contact Contact)" >/dev/null

# Three application passwords on the owner's account: one the owner gives the agent, one the connector uses
# (in its own container, when the setup has one), and one the checks use after the run. Fixed values, so the request and the checks can name them.
$WP eval '
$user = get_user_by("login", "sunnyside");
$item = fn($name, $pw) => ["uuid" => wp_generate_uuid4(), "app_id" => "", "name" => $name, "password" => wp_fast_hash($pw),
  "created" => time(), "last_used" => null, "last_ip" => null];
update_site_option("using_application_passwords", 1); // set by WordPress when it creates the first one
update_user_meta($user->ID, "_application_passwords", [$item("Assistant", "{password}"), $item("Connector", "{connector_password}"), $item("Site monitor", "{monitor_password}")]);
'
$WP cache flush
