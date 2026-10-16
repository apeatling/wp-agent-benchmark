# Trevone Surf School are leaving Wix (www.trevonesurf.test). Their content has been copied onto the new WordPress
# site already, with WordPress's own page addresses; nothing has been done about the old addresses.
$WP user update 1 --user_email=surf@trevonesurf.test --display_name="Lucy Hocking" --first_name=Lucy --last_name=Hocking --skip-email
$WP option update admin_email surf@trevonesurf.test
$WP option update blogname "Trevone Surf School"
$WP option update blogdescription "Surf lessons on Trevone Beach"
$WP post delete 1 2 --force
$WP eval-file /opt/wpab/seed/request-files/migrate.php
