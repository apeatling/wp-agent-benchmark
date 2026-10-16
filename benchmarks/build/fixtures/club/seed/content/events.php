<?php
/** The club's upcoming events in The Events Calendar, at the clubhouse. */
$venue = tribe_create_venue( array( 'Venue' => 'Portwen Sailing Club clubhouse', 'Address' => 'The Slipway, Beach Road', 'City' => 'Portwen', 'Country' => 'United Kingdom', 'post_status' => 'publish' ) );
$events = array(
	array( 'Laying-up supper', '2026-10-31 19:00', '2026-10-31 23:00', 'Our end of season supper and prize-giving. Two courses, £18 a head; tickets from the clubhouse bar.' ),
	array( 'Frostbite series: race 1', '2026-11-01 11:00', '2026-11-01 13:00', 'The first race of the winter series. Briefing at 10.30am.' ),
	array( 'Annual General Meeting', '2026-11-20 19:30', '2026-11-20 21:30', 'The club AGM. The agenda and accounts are on the noticeboard.' ),
	array( 'Christmas social', '2026-12-12 19:00', '2026-12-12 23:00', 'Mince pies, mulled wine and a raffle. Partners and families welcome.' ),
	array( 'Boxing Day pursuit race', '2026-12-26 11:00', '2026-12-26 13:00', 'Fancy dress optional, mince pies compulsory. Any boat, any helm.' ),
);
foreach ( $events as $e ) {
	$id = tribe_create_event(
		array(
			'post_title'     => $e[0],
			'post_content'   => '<p>' . $e[3] . '</p>',
			'post_status'    => 'publish',
			'post_author'    => 1,
			'EventStartDate' => substr( $e[1], 0, 10 ),
			'EventStartHour' => substr( $e[1], 11, 2 ),
			'EventStartMinute' => substr( $e[1], 14, 2 ),
			'EventEndDate'   => substr( $e[2], 0, 10 ),
			'EventEndHour'   => substr( $e[2], 11, 2 ),
			'EventEndMinute' => substr( $e[2], 14, 2 ),
			'EventTimezone'  => 'Europe/London',
			'Venue'          => array( 'VenueID' => $venue ),
		)
	);
	if ( ! $id ) {
		WP_CLI::error( 'Could not create ' . $e[0] );
	}
}
