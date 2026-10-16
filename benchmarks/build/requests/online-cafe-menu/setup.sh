# The Corner Cup's site, made a while ago on its host's one-click WordPress: three pages, with the menu as a PDF
# linked from the front page.
$WP user update 1 --user_email=hello@thecornercup.test --display_name="Megan Rowe" --first_name=Megan --last_name=Rowe --skip-email
$WP option update admin_email hello@thecornercup.test
$WP option update blogname "The Corner Cup"
$WP option update blogdescription "Coffee, breakfast and lunch on Fore Street"
$WP post delete 1 2 --force
pdf=$($WP media import /opt/wpab/seed/request-files/menu.pdf --title="The Corner Cup menu" --porcelain)
url=$($WP eval "echo wp_get_attachment_url($pdf);")
page() { printf '%s' "$3" > /tmp/page.html; $WP post create /tmp/page.html --post_type=page --post_status=publish --post_title="$1" --post_name="$2" --porcelain; }
home=$(page "Welcome to The Corner Cup" home "<!-- wp:paragraph -->
<p>We're a little café on the corner of Fore Street and Chapel Hill, serving coffee, breakfast and lunch six days a week.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Everything's made in our kitchen each morning, and the coffee comes from Tidewater Roasters down the road.</p>
<!-- /wp:paragraph -->

<!-- wp:file {\"id\":$pdf,\"href\":\"$url\"} -->
<div class=\"wp-block-file\"><a href=\"$url\">See our menu</a><a href=\"$url\" class=\"wp-block-file__button wp-element-button\" download>Download</a></div>
<!-- /wp:file -->")
page "About us" about "<!-- wp:paragraph -->
<p>Megan opened The Corner Cup in 2019 after ten years working in cafés around Bristol. We're dog friendly, there's a highchair or two, and the window seats go fast on a Saturday.</p>
<!-- /wp:paragraph -->" >/dev/null
page "Find us" find-us "<!-- wp:paragraph -->
<p>1 Fore Street, Portwen PW1 2AB. Open Monday to Saturday, 8am to 4pm.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Call us on 01632 960318 or email hello@thecornercup.test.</p>
<!-- /wp:paragraph -->" >/dev/null
$WP option update show_on_front page
$WP option update page_on_front "$home"
rm /tmp/page.html
