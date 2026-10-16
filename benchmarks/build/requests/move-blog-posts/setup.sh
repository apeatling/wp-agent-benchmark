# Tregenna Farm Shop are moving their old site (www.tregennafarm.test) onto WordPress. The pages are done, and
# there's a News page for the blog, but none of the old posts are on it yet.
$WP user update 1 --user_email=shop@tregennafarm.test --display_name="Kate Tregenna" --first_name=Kate --last_name=Tregenna --skip-email
$WP option update admin_email shop@tregennafarm.test
$WP option update blogname "Tregenna Farm Shop"
$WP option update blogdescription "Our own meat, veg and eggs near St Mabyn"
$WP post delete 1 2 --force
page() { printf '%s' "$3" > /tmp/page.html; $WP post create /tmp/page.html --post_type=page --post_status=publish --post_title="$1" --post_name="$2" --porcelain; }
home=$(page "Welcome to Tregenna" home "<!-- wp:paragraph -->
<p>A family farm shop near St Mabyn, selling our own meat, veg and eggs since 1998.</p>
<!-- /wp:paragraph -->")
page "Visit us" visit "<!-- wp:paragraph -->
<p>Open every day 9am to 5pm. Free parking in the yard.</p>
<!-- /wp:paragraph -->" >/dev/null
news=$(page "News" news "")
$WP option update show_on_front page
$WP option update page_on_front "$home"
$WP option update page_for_posts "$news"
rm /tmp/page.html
