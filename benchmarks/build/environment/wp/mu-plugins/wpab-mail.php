<?php
/**
 * Stands in for the host's mail: everything the site sends goes to the run's mail catcher (Mailpit, the
 * "mail" service), where the checks read it. Nothing leaves the sandbox. A real host would deliver it.
 */
add_action(
	'phpmailer_init',
	function ( $mailer ) {
		$mailer->isSMTP();
		$mailer->Host     = 'mail';
		$mailer->Port     = 1025;
		$mailer->SMTPAuth = false;
		$mailer->SMTPAutoTLS = false;
	},
	PHP_INT_MAX
);
