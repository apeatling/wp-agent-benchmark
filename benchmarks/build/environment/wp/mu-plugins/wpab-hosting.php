<?php
/**
 * Stands in for hosting. Hosts serve sites over HTTPS, which WordPress needs before it allows application
 * passwords; this site is plain HTTP inside the sandbox network, so they're allowed without it.
 */
add_filter( 'wp_is_application_passwords_available', '__return_true' );
