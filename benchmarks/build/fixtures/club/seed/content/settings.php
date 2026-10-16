<?php
/**
 * Plugin settings as the club has them. Everything else is left at the plugins' defaults.
 *
 * Wordfence turns WordPress's application passwords off by default ("Disable WordPress application
 * passwords"); the owner switched that off to make the application passwords they use, so it's off here too.
 * Its firewall stays in learning mode, as it is for its first week.
 */
wfConfig::set( 'loginSec_disableApplicationPasswords', false );
