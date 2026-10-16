<?php
/**
 * Plugin Name: Sunnyside Specials
 * Description: Shows this week's specials with [sunnyside_specials].
 * Version: 1.2.0
 * Author: Sunnyside Bakery
 */

add_shortcode( 'sunnyside_specials', function () {
	$specials = get_option( 'sunnyside_specials_list', array( 'items' => array() ) );
	return '<p class="specials">This week: ' . esc_html( implode( ', ', (array) $specials['items'] ) ) . '</p>';
} );
