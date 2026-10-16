<?php
/**
 * Records every request the site handles, one JSON line each, in /var/log/wpab/activity.jsonl: what was asked
 * for (page, REST route, connector call, dashboard screen), the answer WordPress gave (status code, any PHP
 * fatal error) and who asked (the agent's application password, the checks, a dashboard login, or a visitor).
 * Collected after the run. It's how a run shows what the agent tried and where WordPress said no, the same way
 * for every agent and harness.
 *
 * Passwords, nonces and tokens are never written. Request bodies are summarised by their keys, plus the values
 * of a few fields that say what was changed (status, roles, plugin, slug).
 */

if ( defined( 'WP_CLI' ) && WP_CLI ) {
	return; // seeding, not the run
}

$GLOBALS['wpab_activity'] = array(
	't'      => microtime( true ),
	'method' => $_SERVER['REQUEST_METHOD'] ?? '',
	'path'   => wpab_activity_path( $_SERVER['REQUEST_URI'] ?? '' ),
	// The checks carry their key (see wpab-monitor.php); a request can't pass as theirs without it.
	'from'   => ( defined( 'WPAB_MONITOR_KEY' ) && hash_equals( WPAB_MONITOR_KEY, (string) ( $_SERVER['HTTP_X_WPAB_MONITOR_KEY'] ?? '' ) ) ) ? 'checks' : null,
	'connector' => ! empty( $_SERVER['HTTP_X_WPAB_CONNECTOR'] ), // sent through the connector container
);

/** The request path and query, with the values of anything secret removed. */
function wpab_activity_path( $uri ) {
	$parts = explode( '?', $uri, 2 );
	if ( count( $parts ) < 2 ) {
		return $uri;
	}
	parse_str( $parts[1], $q );
	foreach ( $q as $k => $v ) {
		if ( preg_match( '/nonce|pass|pwd|token|key|secret|auth/i', $k ) ) {
			$q[ $k ] = '…';
		}
	}
	return $parts[0] . '?' . http_build_query( $q );
}

/** What kind of request this is, from its path. */
function wpab_activity_kind( $path, $route ) {
	if ( $route !== null ) {
		return str_starts_with( $route, '/mcp' ) ? 'connector' : 'api';
	}
	if ( str_contains( $path, '/wp-json' ) || str_contains( $path, 'rest_route=' ) ) {
		return 'api';
	}
	if ( str_contains( $path, 'wp-login.php' ) ) {
		return 'login';
	}
	if ( str_contains( $path, 'admin-ajax.php' ) ) {
		return 'ajax';
	}
	if ( str_contains( $path, '/wp-admin' ) ) {
		return 'dashboard';
	}
	if ( str_contains( $path, 'xmlrpc.php' ) ) {
		return 'xmlrpc';
	}
	if ( str_contains( $path, 'wp-cron.php' ) ) {
		return 'cron';
	}
	return 'page';
}

// REST: the route, and a summary of what was sent.
add_filter( 'rest_pre_dispatch', function ( $result, $server, $request ) {
	$GLOBALS['wpab_activity']['route'] = $request->get_route();
	$params = array_merge( (array) $request->get_body_params(), (array) $request->get_json_params() );
	$GLOBALS['wpab_activity']['sent'] = array_values( array_diff( array_keys( $params ), array( 'password' ) ) );
	foreach ( array( 'status', 'roles', 'plugin', 'slug', 'force', 'reassign' ) as $k ) {
		if ( isset( $params[ $k ] ) ) {
			$GLOBALS['wpab_activity']['values'][ $k ] = $params[ $k ];
		}
	}
	// A connector call (any JSON-RPC request, whatever the plugin's route): the MCP method, the tool, and the
	// ability or inner tool when the tool is a gateway to others.
	$body = json_decode( $request->get_body(), true );
	if ( is_array( $body ) && isset( $body['jsonrpc'] ) ) {
		$args = $body['params']['arguments'] ?? array();
		$GLOBALS['wpab_activity']['mcp'] = array_filter( array(
			'method'  => $body['method'] ?? null,
			'tool'    => $body['params']['name'] ?? null,
			'ability' => is_array( $args ) ? ( $args['ability_name'] ?? $args['tool_name'] ?? $args['tool'] ?? $args['name'] ?? null ) : null,
		), 'is_string' );
	}
	return $result;
}, 1, 3 );

// Dashboard and AJAX: the action asked for.
add_action( 'admin_init', function () {
	foreach ( array( 'action', 'page', 'plugin', 'file' ) as $k ) {
		if ( isset( $_REQUEST[ $k ] ) && is_string( $_REQUEST[ $k ] ) ) {
			$GLOBALS['wpab_activity']['values'][ $k ] = sanitize_text_field( wp_unslash( $_REQUEST[ $k ] ) );
		}
	}
} );

register_shutdown_function( function () {
	$a = $GLOBALS['wpab_activity'];
	$a['status'] = http_response_code() ?: 200;
	$a['kind']   = $a['connector'] ? 'connector' : wpab_activity_kind( $a['path'], $a['route'] ?? null );
	unset( $a['connector'] );
	// Who: the checks, an application password (by its name), a dashboard login, or a visitor.
	$user = function_exists( 'wp_get_current_user' ) ? wp_get_current_user() : null;
	if ( $user && $user->ID ) {
		$a['user'] = $user->user_login;
		$a['role'] = implode( ',', $user->roles );
		$uuid      = $GLOBALS['wp_rest_application_password_uuid'] ?? null;
		if ( $uuid && class_exists( 'WP_Application_Passwords' ) ) {
			$item = WP_Application_Passwords::get_user_application_password( $user->ID, $uuid );
			$a['via'] = $item ? 'application password: ' . $item['name'] : 'application password';
		} elseif ( $a['kind'] === 'connector' ) {
			$a['via'] = 'connector';
		} else {
			$a['via'] = 'dashboard login';
		}
	}
	if ( ! $a['from'] && $a['kind'] === 'cron' ) {
		$a['from'] = 'site'; // WordPress's own scheduled tasks
	}
	if ( ! $a['from'] ) {
		$a['from'] = ( $a['via'] ?? '' ) === 'application password: Site monitor' ? 'checks' : ( isset( $a['user'] ) ? 'agent' : 'visitor' );
	}
	$err = error_get_last();
	if ( $err && in_array( $err['type'], array( E_ERROR, E_PARSE, E_CORE_ERROR, E_COMPILE_ERROR, E_USER_ERROR ), true ) ) {
		$a['fatal'] = substr( $err['message'], 0, 200 ) . ' in ' . basename( $err['file'] );
		$a['status'] = 500;
	}
	$a['ms'] = (int) round( ( microtime( true ) - $a['t'] ) * 1000 );
	@file_put_contents( '/var/log/wpab/activity.jsonl', wp_json_encode( array_filter( $a, fn( $v ) => $v !== null ) ) . "\n", FILE_APPEND | LOCK_EX );
} );
