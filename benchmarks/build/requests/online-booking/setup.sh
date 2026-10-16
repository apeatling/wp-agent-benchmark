# Ruth Kellow's garden design site, made on her host's one-click WordPress a couple of years ago: four pages and a
# contact form that emails her.
$WP user update 1 --user_email=ruth@kellowgardens.test --display_name="Ruth Kellow" --first_name=Ruth --last_name=Kellow --skip-email
$WP option update admin_email ruth@kellowgardens.test
$WP option update blogname "Ruth Kellow Garden Design"
$WP option update blogdescription "Gardens for real life in Cornwall"
$WP post delete 1 2 --force
/opt/wpab/install.sh plugin /opt/wpab/seed/request-plugins.txt
form=$($WP post list --post_type=wpcf7_contact_form --field=ID | head -1)
page() { printf '%s' "$3" > /tmp/page.html; $WP post create /tmp/page.html --post_type=page --post_status=publish --post_title="$1" --post_name="$2" --porcelain; }
home=$(page "Gardens for real life" home "<!-- wp:paragraph -->
<p>I design gardens across Cornwall that are easy to look after and lovely to be in, from small courtyards to whole hillsides.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Every garden starts with a conversation about how you want to use it. <a href=\"/contact/\">Get in touch</a> and tell me about yours.</p>
<!-- /wp:paragraph -->")
page "About Ruth" about "<!-- wp:paragraph -->
<p>I trained at the Eden Project and have been designing gardens for fifteen years. I work with local landscapers and nurseries, and I'm happy to stay involved from the first sketch to the last plant going in.</p>
<!-- /wp:paragraph -->" >/dev/null
page "Gardens" gardens "<!-- wp:paragraph -->
<p>A seaside courtyard in St Ives, a family garden in Truro with room for a trampoline, and a wildlife meadow on a slope near Fowey.</p>
<!-- /wp:paragraph -->" >/dev/null
page "Contact" contact "<!-- wp:paragraph -->
<p>Email ruth@kellowgardens.test or send me a message here and I'll get back to you within a couple of days.</p>
<!-- /wp:paragraph -->

<!-- wp:shortcode -->
[contact-form-7 id=\"$form\" title=\"Contact form 1\"]
<!-- /wp:shortcode -->" >/dev/null
$WP option update show_on_front page
$WP option update page_on_front "$home"
rm /tmp/page.html
