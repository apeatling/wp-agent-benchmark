# Porthallow Village Hall's site, set up by a volunteer a couple of years ago: a front page, hiring the hall and
# how to get in touch. Nothing on it yet about what's on each week.
$WP user update 1 --user_email=hello@porthallowhall.test --display_name="Jan Trewin" --first_name=Jan --last_name=Trewin --skip-email
$WP option update admin_email hello@porthallowhall.test
$WP option update blogname "Porthallow Village Hall"
$WP option update blogdescription "The hall at the heart of the village"
$WP post delete 1 2 --force
page() { printf '%s' "$3" > /tmp/page.html; $WP post create /tmp/page.html --post_type=page --post_status=publish --post_title="$1" --post_name="$2" --porcelain; }
home=$(page "Welcome to Porthallow Village Hall" home "<!-- wp:paragraph -->
<p>Porthallow Village Hall is run by volunteers for everyone in the village and round about. It was built in 1923 and has had a new kitchen and toilets since, but the roof is next on the list.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>There's something on most days of the week, and the hall can be hired for parties, meetings and classes.</p>
<!-- /wp:paragraph -->")
page "Hire the hall" hire-the-hall "<!-- wp:paragraph -->
<p>The main hall seats 80, or 120 standing, and there's a kitchen with a cooker, urn and crockery for 100. There's a car park for about 15 cars.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>It's £12 an hour, or £8 an hour for village groups. To book, ring Jan on 01632 960587.</p>
<!-- /wp:paragraph -->" >/dev/null
page "Contact" contact "<!-- wp:paragraph -->
<p>Porthallow Village Hall, Church Road, Porthallow PW4 7JD.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>For bookings or anything else, ring Jan on 01632 960587.</p>
<!-- /wp:paragraph -->" >/dev/null
$WP option update show_on_front page
$WP option update page_on_front "$home"
rm /tmp/page.html
