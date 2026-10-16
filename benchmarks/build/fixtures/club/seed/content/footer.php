<?php
/** The footer: Astra's footer builder with two widget columns (the club's address, useful links) above the copyright line. */
$settings = get_option( 'astra-settings', array() );
$settings['footer-desktop-items'] = array(
	'above'   => array( 'above_1' => array(), 'above_2' => array(), 'above_3' => array(), 'above_4' => array(), 'above_5' => array() ),
	'primary' => array( 'primary_1' => array( 'widget-1' ), 'primary_2' => array( 'widget-2' ), 'primary_3' => array(), 'primary_4' => array(), 'primary_5' => array() ),
	'below'   => array( 'below_1' => array( 'copyright' ), 'below_2' => array(), 'below_3' => array(), 'below_4' => array(), 'below_5' => array() ),
);
$settings['hb-footer-column'] = '2';
$settings['hb-footer-layout'] = array( 'desktop' => '2-equal', 'tablet' => '2-equal', 'mobile' => 'full' );
update_option( 'astra-settings', $settings );

update_option(
	'widget_text',
	array(
		2              => array(
			'title'  => 'Portwen Sailing Club',
			'text'   => "The Slipway, Beach Road, Portwen\nAn RYA Recognised Training Centre\nAffiliated to the Royal Yachting Association",
			'filter' => true,
			'visual' => true,
		),
		3              => array(
			'title'  => 'Useful links',
			'text'   => "<a href=\"https://www.rya.org.uk/\">Royal Yachting Association</a>\n<a href=\"https://www.metoffice.gov.uk/weather/specialist-forecasts/coast-and-sea/inshore-waters-forecast\">Inshore waters forecast</a>\n<a href=\"/contact/\">Contact us</a>",
			'filter' => true,
			'visual' => true,
		),
		'_multiwidget' => 1,
	)
);
$sidebars                     = get_option( 'sidebars_widgets', array() );
$sidebars['footer-widget-1']  = array( 'text-2' );
$sidebars['footer-widget-2']  = array( 'text-3' );
update_option( 'sidebars_widgets', $sidebars );
