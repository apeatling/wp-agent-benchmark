# The cake pages have got slow: the owner pasted full-size photos from the camera into each cake's description, and
# a delivery-date plugin they added last month asks a courier's server for the next slot on every product page,
# waiting up to four seconds each time for a server that doesn't answer.
cp -r /opt/wpab/seed/request-files/sunnyside-delivery wp-content/plugins/
$WP plugin activate sunnyside-delivery
# Camera photos: 2400 by 1800, saved at full quality, three for each cake.
for slug in chocolate-celebration-cake victoria-sponge lemon-drizzle-loaf; do
  imgs=""
  for n in 1 2 3; do
    f=/tmp/$slug-$n.jpg
    php -r '
      mt_srand(crc32($argv[1]));
      $w = 2400; $h = 1800; $im = imagecreatetruecolor($w, $h);
      for ($y = 0; $y < $h; $y += 2) { for ($x = 0; $x < $w; $x += 2) {
        $c = imagecolorallocate($im, 150 + mt_rand(0, 90), 100 + mt_rand(0, 80), 60 + mt_rand(0, 60));
        imagefilledrectangle($im, $x, $y, $x + 1, $y + 1, $c); } }
      imagejpeg($im, $argv[1], 98);' "$f"
    id=$($WP media import "$f" --title="IMG_$((4000 + n))" --porcelain)
    url=$($WP eval "echo wp_get_attachment_url($id);")
    imgs="$imgs<p><img src=\"$url\" alt=\"\" /></p>"
    rm -f "$f"
  done
  pid=$($WP post list --post_type=product --name=$slug --field=ID)
  desc=$($WP post get "$pid" --field=post_content)
  printf '%s' "$desc$imgs" > /tmp/desc.html
  $WP post update "$pid" /tmp/desc.html >/dev/null
done
rm -f /tmp/desc.html
