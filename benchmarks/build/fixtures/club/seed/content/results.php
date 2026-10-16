<?php
/** This season's Sunday series standings, as a TablePress table. Prints the table's ID for the Results page. */
$table         = TablePress::$model_table->get_table_template();
$table['name'] = 'Sunday series 2026';
$table['description'] = 'Overall standings after discards.';
$table['data'] = array(
	array( 'Place', 'Helm', 'Crew', 'Class', 'Sail no.', 'Points' ),
	array( '1', 'Mark Jenkin', '', 'ILCA 7', '214877', '11' ),
	array( '2', 'Lowenna Hichens', 'Ellie Pascoe', 'RS Feva', '6631', '17' ),
	array( '3', 'Rob Tonkin', '', 'ILCA 6', '201356', '22' ),
	array( '4', 'Will Cocking', 'Sam Cocking', 'Wayfarer', '11082', '29' ),
	array( '5', 'Kerensa Bray', '', 'Topper', '48120', '31' ),
	array( '6', 'Jamie Uren', '', 'ILCA 6', '196540', '38' ),
	array( '7', 'Chris Angove', 'Becky Laity', 'Merlin Rocket', '3644', '42' ),
	array( '8', 'Tamsin Rule', '', 'Topper', '47702', '47' ),
);
$table['visibility']['rows']    = array_fill( 0, 9, 1 );
$table['visibility']['columns'] = array_fill( 0, 6, 1 );
$id = TablePress::$model_table->add( $table );
if ( is_wp_error( $id ) ) {
	WP_CLI::error( $id->get_error_message() );
}
echo $id;
