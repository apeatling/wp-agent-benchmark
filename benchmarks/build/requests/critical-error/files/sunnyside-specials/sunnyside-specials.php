<?php
/**
 * Plugin Name: Sunnyside Specials
 * Description: Shows this week's specials with [sunnyside_specials], or the Specials block.
 * Version: 1.3.0
 * Author: Sunnyside Bakery
 */

require_once __DIR__ . '/includes/block.php';

add_shortcode( 'sunnyside_specials', 'sunnyside_specials_render' );

function sunnyside_specials_render() {
	$specials = get_option( 'sunnyside_specials_list', array( 'items' => array() ) );
	return '<p class="specials">This week: ' . esc_html( implode( ', ', (array) $specials['items'] ) ) . '</p>';
}

sunnyside_specials_register_blocks();
