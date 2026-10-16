# The owner has just got a new WordPress site from their host, with nothing done to it yet, to replace the old
# hand-built one (www.quaysidephysio.test).
$WP user update 1 --user_email=info@quaysidephysio.test --display_name="Anna Carne" --first_name=Anna --last_name=Carne --skip-email
$WP option update admin_email info@quaysidephysio.test
