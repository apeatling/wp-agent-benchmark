<?php
/**
 * Plugin Name: Sunnyside Delivery Dates
 * Description: Shows the next delivery date on product pages, from the courier's API.
 * Version: 1.0.4
 * Author: Sunnyside Bakery
 */

// Asks the courier for the next delivery slot every time a product page is shown, and waits for the answer.
add_action( 'woocommerce_single_product_summary', function () {
	$response = wp_remote_get( 'http://10.255.255.1/v1/next-slot?postcode=PW1', array( 'timeout' => 4 ) );
	$slot     = is_wp_error( $response ) ? '' : json_decode( wp_remote_retrieve_body( $response ), true )['date'] ?? '';
	echo '<p class="delivery">' . ( $slot ? 'Next delivery: ' . esc_html( $slot ) : 'Delivery or collection from the shop.' ) . '</p>';
}, 25 );
