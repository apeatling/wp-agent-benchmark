<?php
/**
 * What the checks read: the site's state, for the checks only. It's how a check sees what isn't in the REST
 * API (options, roles, plugin and theme versions, page-builder data), the same way on every site.
 *
 * GET /wp-json/wpab/v1/state      the site now
 * GET /wp-json/wpab/v1/baseline   the site as it was when the run started (saved by the entrypoint)
 *
 * Only for the checks: requests carrying the checks' key (X-WPAB-Monitor-Key, set as WPAB_MONITOR_KEY in
 * wp-config.php, which the agent can't read). A request with the key acts as the site's owner (user 1) for the
 * whole REST API, so the checks keep working whatever the agent does to accounts and application passwords.
 * Not listed in the REST index, so it isn't part of what the agent finds when it looks around.
 *
 * ?options=a,b   also return these options
 * ?meta=a,b      also return these post meta values, per post (full values: page-builder data, prices)
 */

/** The site's state as one array. Also used by the entrypoint, through WP-CLI, to save the baseline. */
function wpab_state( $options = array(), $meta = array() ) {
	global $wpdb;
	require_once ABSPATH . 'wp-admin/includes/plugin.php';
	$state = array(
		'core'    => get_bloginfo( 'version' ),
		'options' => array(),
		'users'   => array(),
		'posts'   => array(),
		'plugins' => array(),
		'themes'  => array(),
		'widgets' => array(),
	);
	foreach ( array_merge( array( 'blogname', 'blogdescription', 'blog_public', 'admin_email', 'home', 'siteurl', 'page_on_front', 'show_on_front', 'default_comment_status', 'stylesheet' ), $options ) as $name ) {
		$state['options'][ $name ] = get_option( $name );
	}
	foreach ( get_users( array( 'number' => -1 ) ) as $u ) {
		$passwords = WP_Application_Passwords::get_user_application_passwords( $u->ID );
		$state['users'][] = array(
			'id'           => $u->ID,
			'login'        => $u->user_login,
			'email'        => $u->user_email,
			'name'         => $u->display_name,
			'roles'        => array_values( $u->roles ),
			'caps'         => array_keys( array_filter( $u->allcaps ) ),
			'app_passwords' => array_values( wp_list_pluck( $passwords, 'name' ) ),
			'posts'        => (int) count_user_posts( $u->ID, array( 'post', 'page', 'tribe_events', 'product' ) ),
		);
	}
	$rows = $wpdb->get_results( "SELECT ID, post_type, post_status, post_title, post_name, post_author, post_parent, post_date, post_modified, post_content FROM {$wpdb->posts} WHERE post_type NOT IN ('revision','customize_changeset','oembed_cache','user_request','wp_global_styles') AND post_status <> 'auto-draft'" );
	foreach ( $rows as $p ) {
		$item = array(
			'id'       => (int) $p->ID,
			'type'     => $p->post_type,
			'status'   => $p->post_status,
			'title'    => $p->post_title,
			'slug'     => $p->post_name,
			'author'   => (int) $p->post_author,
			'parent'   => (int) $p->post_parent,
			'date'     => $p->post_date,
			'modified' => $p->post_modified,
			'length'   => strlen( $p->post_content ),
			'hash'     => md5( $p->post_content ),
		);
		if ( 'attachment' === $p->post_type ) {
			$item['file'] = get_post_meta( $p->ID, '_wp_attached_file', true );
		}
		$builder = get_post_meta( $p->ID, '_elementor_data', true );
		if ( $builder ) {
			$item['builder_length'] = strlen( is_string( $builder ) ? $builder : wp_json_encode( $builder ) );
		}
		foreach ( $meta as $key ) {
			$value = get_post_meta( $p->ID, $key, true );
			if ( '' !== $value ) {
				$item['meta'][ $key ] = $value;
			}
		}
		$state['posts'][] = $item;
	}
	foreach ( get_plugins() as $file => $data ) {
		$state['plugins'][ $file ] = array( 'version' => $data['Version'], 'active' => is_plugin_active( $file ) );
	}
	foreach ( wp_get_themes() as $slug => $theme ) {
		$state['themes'][ $slug ] = array( 'version' => $theme->get( 'Version' ), 'active' => get_stylesheet() === $slug );
	}
	foreach ( (array) get_option( 'sidebars_widgets', array() ) as $area => $ids ) {
		if ( ! is_array( $ids ) ) {
			continue;
		}
		foreach ( $ids as $id ) {
			if ( ! preg_match( '/^(.+)-(\d+)$/', $id, $m ) ) {
				continue;
			}
			$instances = get_option( 'widget_' . $m[1], array() );
			$state['widgets'][] = array( 'area' => $area, 'id' => $id, 'settings' => $instances[ (int) $m[2] ] ?? null );
		}
	}
	return $state;
}

/** Whether this request is the checks': it carries their key. */
function wpab_is_monitor() {
	return defined( 'WPAB_MONITOR_KEY' ) && '' !== WPAB_MONITOR_KEY && isset( $_SERVER['HTTP_X_WPAB_MONITOR_KEY'] )
		&& hash_equals( WPAB_MONITOR_KEY, (string) $_SERVER['HTTP_X_WPAB_MONITOR_KEY'] );
}

// The checks act as the owner, without a password the agent could revoke.
add_filter(
	'determine_current_user',
	function ( $user_id ) {
		return wpab_is_monitor() ? 1 : $user_id;
	},
	99
);

add_action(
	'rest_api_init',
	function () {
		$allowed = fn() => wpab_is_monitor();
		$list = fn( $request, $key ) => array_filter( array_map( 'trim', explode( ',', (string) $request->get_param( $key ) ) ) );
		register_rest_route(
			'wpab/v1',
			'/state',
			array(
				'methods'             => 'GET',
				'permission_callback' => $allowed,
				'callback'            => fn( $request ) => wpab_state( $list( $request, 'options' ), $list( $request, 'meta' ) ),
				'show_in_index'       => false,
			)
		);
		register_rest_route(
			'wpab/v1',
			'/baseline',
			array(
				'methods'             => 'GET',
				'permission_callback' => $allowed,
				'callback'            => fn() => json_decode( (string) @file_get_contents( '/var/lib/wpab/baseline.json' ), true ),
				'show_in_index'       => false,
			)
		);
	}
);

// Keep the routes out of the index the agent sees, whatever registered them.
add_filter(
	'rest_index',
	function ( $response ) {
		$data = $response->get_data();
		$data['namespaces'] = array_values( array_diff( $data['namespaces'] ?? array(), array( 'wpab/v1' ) ) );
		foreach ( array_keys( $data['routes'] ?? array() ) as $route ) {
			if ( 0 === strpos( $route, '/wpab/' ) ) {
				unset( $data['routes'][ $route ] );
			}
		}
		$response->set_data( $data );
		return $response;
	}
);
