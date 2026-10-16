<?php
/**
 * The Specials block: the same list as the shortcode, for the block editor.
 */

function sunnyside_specials_register_block() {
	add_action(
		'init',
		function () {
			register_block_type(
				'sunnyside/specials',
				array(
					'title'           => 'Specials',
					'render_callback' => 'sunnyside_specials_render',
				)
			);
		}
	);
}
