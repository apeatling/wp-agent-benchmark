# Polvean Vets are moving their old hand-built site (www.polveanvets.test) onto WordPress. Someone's started:
# the home, services and contact pages are already moved; the About and FAQ pages aren't.
$WP user update 1 --user_email=reception@polveanvets.test --display_name="Sue Pascoe" --first_name=Sue --last_name=Pascoe --skip-email
$WP option update admin_email reception@polveanvets.test
$WP option update blogname "Polvean Veterinary Surgery"
$WP option update blogdescription "Independent vets in Liskeard"
$WP post delete 1 2 --force
page() { printf '%s' "$3" > /tmp/page.html; $WP post create /tmp/page.html --post_type=page --post_status=publish --post_title="$1" --post_name="$2" --porcelain; }
home=$(page "Caring for Liskeard's pets since 1987" home "<!-- wp:paragraph -->
<p>We're a friendly, independent vets on Station Road, open six days a week.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p><a href=\"/contact/\">Book an appointment</a></p>
<!-- /wp:paragraph -->")
page "Services" services "<!-- wp:paragraph -->
<p>Vaccinations, neutering, dentistry, X-ray, microchipping, nurse clinics and weight checks.</p>
<!-- /wp:paragraph -->" >/dev/null
page "Contact us" contact "<!-- wp:paragraph -->
<p>14 Station Road, Liskeard PL14 4BZ. Tel 01579 340212. Email reception@polveanvets.test.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Monday to Friday 8.30am to 6.30pm, Saturday 9am to 12pm.</p>
<!-- /wp:paragraph -->" >/dev/null
$WP option update show_on_front page
$WP option update page_on_front "$home"
rm /tmp/page.html
