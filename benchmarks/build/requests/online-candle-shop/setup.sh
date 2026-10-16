# Little Harbour Candles' site, made on the host's one-click WordPress: three pages, no shop yet.
$WP user update 1 --user_email=jess@littleharbourcandles.test --display_name="Jess Tremayne" --first_name=Jess --last_name=Tremayne --skip-email
$WP option update admin_email jess@littleharbourcandles.test
$WP option update blogname "Little Harbour Candles"
$WP option update blogdescription "Hand-poured soy candles from Cornwall"
$WP post delete 1 2 --force
page() { printf '%s' "$3" > /tmp/page.html; $WP post create /tmp/page.html --post_type=page --post_status=publish --post_title="$1" --post_name="$2" --porcelain; }
home=$(page "Hand-poured in Cornwall" home "<!-- wp:paragraph -->
<p>We make soy wax candles in small batches in our workshop above the harbour, scented with the smells of the Cornish coast.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>You'll find us at Portwen market every Saturday, or get in touch to order.</p>
<!-- /wp:paragraph -->")
page "About us" about "<!-- wp:paragraph -->
<p>Jess started pouring candles at her kitchen table in 2021. Every candle is made with natural soy wax, a cotton wick and a tin or jar you can reuse.</p>
<!-- /wp:paragraph -->" >/dev/null
page "Contact" contact "<!-- wp:paragraph -->
<p>Email jess@littleharbourcandles.test or find us at Portwen market on Saturdays.</p>
<!-- /wp:paragraph -->" >/dev/null
$WP option update show_on_front page
$WP option update page_on_front "$home"
rm /tmp/page.html
