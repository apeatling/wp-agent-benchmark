<?php
// The Wix site's content, already copied onto WordPress (by whoever started the move): pages and posts with
// WordPress's own addresses, the home page on the front and the blog on its own page.
$pages = json_decode( file_get_contents( __DIR__ . '/pages.json' ), true );
foreach ( $pages as $p ) {
	$content = implode( "\n\n", array_map( fn( $t ) => "<!-- wp:paragraph -->\n<p>$t</p>\n<!-- /wp:paragraph -->", $p['text'] ) );
	$id = wp_insert_post( array(
		'post_type'    => 'post' === $p['kind'] ? 'post' : 'page',
		'post_status'  => 'publish',
		'post_title'   => $p['title'],
		// Posts get WordPress's addresses from their titles, as they did when they were copied.
		'post_name'    => 'post' === $p['kind'] ? '' : $p['slug'],
		'post_content' => $content,
		'post_date'    => isset( $p['date'] ) ? $p['date'] . ' 10:00:00' : current_time( 'mysql' ),
		'post_author'  => 1,
	), true );
	if ( is_wp_error( $id ) ) {
		fwrite( STDERR, $id->get_error_message() );
		exit( 1 );
	}
	if ( 'home' === $p['slug'] ) {
		update_option( 'show_on_front', 'page' );
		update_option( 'page_on_front', $id );
	} elseif ( 'blog' === $p['kind'] ) {
		update_option( 'page_for_posts', $id );
	}
}
