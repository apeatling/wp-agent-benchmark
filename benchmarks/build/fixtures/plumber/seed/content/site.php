<?php
/**
 * Harbour Plumbing and Heating's content, built the way Elementor builds it: each page and the header and footer
 * are saved through Elementor's own document save (the same call its editor makes), so _elementor_data,
 * _elementor_edit_mode, _elementor_version and the plain-text copy in post_content are what the editor writes.
 * Run with WP-CLI as the owner: wp eval-file site.php --user=harbourplumbing. Deterministic: fixed element IDs.
 */

use Elementor\Plugin;

$ids = 0;
$page_key = '';
// Elementor's element IDs are seven hex characters; fixed here so the site is the same every run.
$id = function () use ( &$ids, &$page_key ) {
	return substr( md5( $page_key . ':' . ( ++$ids ) ), 0, 7 );
};
$widget = function ( $type, $settings ) use ( $id ) {
	return array( 'id' => $id(), 'elType' => 'widget', 'settings' => $settings, 'elements' => array(), 'widgetType' => $type );
};
$box = function ( $settings, $elements, $inner = false ) use ( $id ) {
	return array( 'id' => $id(), 'elType' => 'container', 'settings' => $settings, 'elements' => $elements, 'isInner' => $inner );
};
$pad = fn( $top, $side = 20 ) => array( 'unit' => 'px', 'top' => (string) $top, 'right' => (string) $side, 'bottom' => (string) $top, 'left' => (string) $side, 'isLinked' => false );
$navy = '#16324F';
$teal = '#1E8C93';
$phone = '01632 960418';
$tel = array( 'url' => 'tel:01632960418', 'is_external' => '', 'nofollow' => '', 'custom_attributes' => '' );
$link = fn( $path ) => array( 'url' => home_url( $path ), 'is_external' => '', 'nofollow' => '', 'custom_attributes' => '' );
$h = fn( $title, $size = 'h2', $extra = array() ) => $widget( 'heading', array_merge( array( 'title' => $title, 'header_size' => $size ), $extra ) );
$p = fn( $html ) => $widget( 'text-editor', array( 'editor' => $html ) );
$section = fn( $elements, $extra = array() ) => $box( array_merge( array( 'flex_direction' => 'column', 'padding' => $pad( 60 ) ), $extra ), $elements );

/** Save a post's Elementor content through Elementor, as its editor does. */
$save = function ( $post_id, $elements, $template ) {
	update_post_meta( $post_id, '_wp_page_template', $template );
	$document = Plugin::$instance->documents->get( $post_id, false );
	// What opening a page in Elementor's editor does first.
	$document->set_is_built_with_elementor( true );
	if ( ! $document->save( array( 'elements' => $elements, 'settings' => array( 'template' => $template ) ) ) ) {
		WP_CLI::error( "Elementor didn't save post $post_id" );
	}
};
$page = function ( $title, $slug, $elements, $template = 'elementor_header_footer' ) use ( $save, &$page_key, &$ids ) {
	$post_id = wp_insert_post( array( 'post_type' => 'page', 'post_status' => 'publish', 'post_title' => $title, 'post_name' => $slug, 'post_author' => 1 ), true );
	if ( is_wp_error( $post_id ) ) {
		WP_CLI::error( $post_id );
	}
	$save( $post_id, $elements, $template );
	return $post_id;
};

// The contact form: WPForms' simple contact form, as the freelancer set it up. Notifications go to the site's
// admin email, WPForms' default. Its JavaScript-only anti-spam token is off, so the form also works for
// visitors without JavaScript (and for the checks, which post it the way a browser without scripts would).
$form_id = wpforms()->obj( 'form' )->add( 'Contact form', array(), array( 'template' => 'simple-contact-form-template' ) );
wpforms()->obj( 'form' )->update(
	$form_id,
	array(
		'id'       => (string) $form_id,
		'field_id' => 5,
		'fields'   => array(
			'1' => array( 'id' => '1', 'type' => 'name', 'label' => 'Your name', 'format' => 'simple', 'required' => '1', 'size' => 'medium' ),
			'2' => array( 'id' => '2', 'type' => 'email', 'label' => 'Email', 'required' => '1', 'size' => 'medium' ),
			'3' => array( 'id' => '3', 'type' => 'text', 'label' => 'Phone number', 'size' => 'medium' ),
			'4' => array( 'id' => '4', 'type' => 'textarea', 'label' => 'How can we help?', 'required' => '1', 'size' => 'medium',
				'description' => 'Tell us what the problem is and roughly where you are.' ),
		),
		'settings' => array(
			'form_title'             => 'Contact form',
			'form_desc'              => '',
			'submit_text'            => 'Send enquiry',
			'submit_text_processing' => 'Sending...',
			'antispam'               => '0',
			'antispam_v3'            => '0',
			'ajax_submit'            => '1',
			'notification_enable'    => '1',
			'notifications'          => array(
				'1' => array(
					'notification_name' => 'Default Notification',
					'email'             => '{admin_email}',
					'subject'           => 'New enquiry from the website',
					'sender_name'       => 'Harbour Plumbing website',
					'sender_address'    => '{admin_email}',
					'replyto'           => '{field_id="2"}',
					'message'           => '{all_fields}',
				),
			),
			'confirmations'          => array(
				'1' => array( 'type' => 'message', 'message' => "<p>Thanks, we've got your message. We'll get back to you, usually the same day.</p>", 'message_scroll' => '1' ),
			),
		),
		'meta'     => array( 'template' => 'simple-contact-form-template' ),
	)
);

$page_key = 'home';
$home = $page(
	'Home',
	'home',
	array(
		$section(
			array(
				$h( 'Plumbing and heating in Portwen and West Cornwall', 'h1', array( 'title_color' => '#FFFFFF' ) ),
				$p( "<p><span style=\"color: #ffffff;\">We're Harbour Plumbing and Heating, a family firm with two vans and over twenty years in the trade. Boilers, leaks, bathrooms and everything in between, done properly and cleaned up after.</span></p>" ),
				$box(
					array( 'flex_direction' => 'row', 'flex_gap' => array( 'unit' => 'px', 'size' => 15, 'column' => '15', 'row' => '15' ) ),
					array(
						$widget( 'button', array( 'text' => 'Get in touch', 'link' => $link( '/contact/' ), 'background_color' => $teal ) ),
						$widget( 'button', array( 'text' => 'Call ' . $phone, 'link' => $tel, 'background_color' => '#FFFFFF', 'button_text_color' => $navy ) ),
					),
					true
				),
			),
			array( 'background_background' => 'classic', 'background_color' => $navy, 'padding' => $pad( 100 ) )
		),
		$section(
			array(
				$h( 'What we do', 'h2', array( 'align' => 'center' ) ),
				$box(
					array( 'flex_direction' => 'row', 'flex_gap' => array( 'unit' => 'px', 'size' => 30, 'column' => '30', 'row' => '30' ) ),
					array(
						$widget( 'icon-box', array( 'selected_icon' => array( 'value' => 'fas fa-fire', 'library' => 'fa-solid' ), 'title_text' => 'Boilers',
							'description_text' => 'Servicing, repairs and new boilers. We service most makes of gas boiler.', 'link' => $link( '/services/' ) ) ),
						$widget( 'icon-box', array( 'selected_icon' => array( 'value' => 'fas fa-clipboard-check', 'library' => 'fa-solid' ), 'title_text' => 'Landlord gas safety',
							'description_text' => 'Gas safety certificates for landlords and letting agents, with reminders when the next one is due.', 'link' => $link( '/services/' ) ) ),
						$widget( 'icon-box', array( 'selected_icon' => array( 'value' => 'fas fa-wrench', 'library' => 'fa-solid' ), 'title_text' => 'Plumbing and repairs',
							'description_text' => 'Leaks, burst pipes, taps, toilets, radiators and bathrooms.', 'link' => $link( '/services/' ) ) ),
					),
					true
				),
			)
		),
		$section(
			array(
				$h( 'Why people use us', 'h2' ),
				$widget( 'icon-list', array( 'icon_list' => array(
					array( '_id' => $id(), 'text' => 'Gas Safe registered engineers', 'selected_icon' => array( 'value' => 'fas fa-check', 'library' => 'fa-solid' ) ),
					array( '_id' => $id(), 'text' => 'Fixed prices for servicing and certificates', 'selected_icon' => array( 'value' => 'fas fa-check', 'library' => 'fa-solid' ) ),
					array( '_id' => $id(), 'text' => 'You talk to us, not a call centre', 'selected_icon' => array( 'value' => 'fas fa-check', 'library' => 'fa-solid' ) ),
					array( '_id' => $id(), 'text' => 'On time, tidy, and we take our rubbish with us', 'selected_icon' => array( 'value' => 'fas fa-check', 'library' => 'fa-solid' ) ),
				) ) ),
				$widget( 'testimonial', array( 'testimonial_content' => 'Gareth came out the same afternoon when our boiler packed up, had it going again in an hour and explained everything. Can\'t recommend them enough.',
					'testimonial_name' => 'Sue P.', 'testimonial_job' => 'Hayle' ) ),
			),
			array( 'background_background' => 'classic', 'background_color' => '#F3F6F8' )
		),
		$section(
			array(
				$h( 'Need a plumber?', 'h2', array( 'align' => 'center' ) ),
				$p( '<p style="text-align: center;">Ring us on ' . $phone . ' or send us a message and we\'ll get back to you, usually the same day.</p>' ),
				$widget( 'button', array( 'text' => 'Contact us', 'link' => $link( '/contact/' ), 'align' => 'center', 'background_color' => $teal ) ),
			)
		),
	)
);

// The price list: one row per service, the name and a line about it on the left and the price on the right.
$page_key = 'services';
$priced = array(
	array( 'Boiler service', 'A full annual service for gas boilers, with a written report. Keeps your manufacturer\'s warranty valid.', '£85' ),
	array( 'Gas safety certificate (CP12)', 'For landlords: checks on the boiler and up to three gas appliances, with the certificate emailed to you.', '£70' ),
	array( 'Hourly rate', 'For general plumbing and repairs, after the call-out. Charged in half-hour steps.', '£60' ),
	array( 'Call-out fee', 'Covers us coming out and the first half hour on site.', '£55' ),
);
$rows = array();
foreach ( $priced as list( $name, $about, $price ) ) {
	$rows[] = $box(
		array( 'flex_direction' => 'row', 'flex_justify_content' => 'space-between', 'flex_align_items' => 'center',
			'border_border' => 'solid', 'border_width' => array( 'unit' => 'px', 'top' => '0', 'right' => '0', 'bottom' => '1', 'left' => '0', 'isLinked' => false ), 'border_color' => '#D9E1E7',
			'padding' => $pad( 18, 0 ) ),
		array(
			$box( array( 'flex_direction' => 'column', 'width' => array( 'unit' => '%', 'size' => 75 ) ), array( $h( $name, 'h3' ), $p( "<p>$about</p>" ) ), true ),
			$h( $price, 'h3', array( 'align' => 'right', 'title_color' => $teal ) ),
		),
		true
	);
}
$services = $page(
	'Services',
	'services',
	array(
		$section(
			array(
				$h( 'Services and prices', 'h1' ),
				$p( '<p>Our prices for the jobs we do most. All prices include VAT. For anything else we\'ll come and have a look and give you a written quote first, free of charge.</p>' ),
			)
		),
		$section( array_merge( array( $h( 'Prices', 'h2' ) ), $rows ), array( 'padding' => $pad( 20 ) ) ),
		$section(
			array(
				$h( 'Other work we do', 'h2' ),
				$p( '<p>Priced after a free visit:</p>' ),
				$widget( 'icon-list', array( 'icon_list' => array(
					array( '_id' => $id(), 'text' => 'New and replacement boilers', 'selected_icon' => array( 'value' => 'fas fa-check', 'library' => 'fa-solid' ) ),
					array( '_id' => $id(), 'text' => 'Bathroom and shower installations', 'selected_icon' => array( 'value' => 'fas fa-check', 'library' => 'fa-solid' ) ),
					array( '_id' => $id(), 'text' => 'Power flushing and radiator work', 'selected_icon' => array( 'value' => 'fas fa-check', 'library' => 'fa-solid' ) ),
					array( '_id' => $id(), 'text' => 'Unvented hot water cylinders', 'selected_icon' => array( 'value' => 'fas fa-check', 'library' => 'fa-solid' ) ),
					array( '_id' => $id(), 'text' => 'Leaks, burst pipes and blocked drains', 'selected_icon' => array( 'value' => 'fas fa-check', 'library' => 'fa-solid' ) ),
				) ) ),
				$widget( 'button', array( 'text' => 'Ask for a quote', 'link' => $link( '/contact/' ), 'background_color' => $teal ) ),
			)
		),
	)
);

$page_key = 'about';
$page(
	'About',
	'about',
	array(
		$section(
			array(
				$h( 'About us', 'h1' ),
				$p( "<p>Gareth Penrose started Harbour Plumbing and Heating in 2009 with one van and a lot of early mornings. His son Rhys joined after finishing his apprenticeship in 2019, and these days there are two vans on the road around Portwen and West Cornwall.</p>\n<p>We're both Gas Safe registered. Most of our work comes from people who've used us before or been told about us by a neighbour, and we'd like to keep it that way: turn up when we say we will, explain what's wrong, and charge what we said we would.</p>" ),
				$h( 'Gas Safe registered', 'h3' ),
				$p( "<p>Always ask to see an engineer's Gas Safe ID card before they work on your boiler or gas appliances. We'll show you ours without being asked.</p>" ),
			)
		),
	)
);

$page_key = 'areas';
$towns = array( 'Portwen', 'Penzance', 'Newlyn', 'Marazion', 'St Ives', 'Carbis Bay', 'Hayle', 'Helston', 'Camborne' );
$page(
	'Areas we cover',
	'areas-we-cover',
	array(
		$section(
			array(
				$p( "<p>We're based in Portwen and cover most of West Cornwall, usually within about half an hour of the yard:</p>" ),
				$widget( 'icon-list', array( 'icon_list' => array_map( fn( $t ) => array( '_id' => $id(), 'text' => $t, 'selected_icon' => array( 'value' => 'fas fa-map-marker-alt', 'library' => 'fa-solid' ) ), $towns ) ) ),
				$p( "<p>Not sure if we come out to you? Give us a ring on $phone and ask.</p>" ),
			)
		),
	),
	'default'
);

$page_key = 'contact';
$contact = $page(
	'Contact',
	'contact',
	array(
		$box(
			array( 'flex_direction' => 'row', 'padding' => $pad( 60 ), 'flex_gap' => array( 'unit' => 'px', 'size' => 40, 'column' => '40', 'row' => '40' ) ),
			array(
				$box(
					array( 'flex_direction' => 'column', 'width' => array( 'unit' => '%', 'size' => 40 ) ),
					array(
						$h( 'Get in touch', 'h1' ),
						$p( "<p><strong>Phone:</strong> $phone<br />Monday to Friday, 8am to 5pm. For emergencies out of hours, ring the same number.</p>\n<p><strong>Yard:</strong> Unit 3, Harbour Road Industrial Estate, Portwen, Cornwall</p>" ),
					),
					true
				),
				$box(
					array( 'flex_direction' => 'column', 'width' => array( 'unit' => '%', 'size' => 60 ) ),
					array(
						$h( 'Send us a message', 'h2' ),
						$widget( 'wpforms', array( 'form_id' => (string) $form_id, 'display_form_name' => '', 'display_form_description' => '' ) ),
					),
					true
				),
			)
		),
	)
);

update_option( 'show_on_front', 'page' );
update_option( 'page_on_front', $home );

// The main menu, used by the header.
$menu = wp_create_nav_menu( 'Main menu' );
foreach ( array( $home, $services, get_page_by_path( 'about' )->ID, get_page_by_path( 'areas-we-cover' )->ID, $contact ) as $i => $pid ) {
	wp_update_nav_menu_item( $menu, 0, array( 'menu-item-object-id' => $pid, 'menu-item-object' => 'page', 'menu-item-type' => 'post_type', 'menu-item-status' => 'publish', 'menu-item-position' => $i + 1 ) );
}

// Header and footer, made with Ultimate Addons (Header Footer Elementor) and shown on the whole site.
$template = function ( $title, $type, $elements ) use ( $save ) {
	$post_id = wp_insert_post( array( 'post_type' => 'elementor-hf', 'post_status' => 'publish', 'post_title' => $title, 'post_author' => 1 ), true );
	update_post_meta( $post_id, 'ehf_template_type', $type );
	update_post_meta( $post_id, 'ehf_target_include_locations', array( 'rule' => array( 'basic-global' ), 'specific' => array() ) );
	update_post_meta( $post_id, 'ehf_target_exclude_locations', array() );
	update_post_meta( $post_id, 'ehf_target_user_roles', array( 'all' ) );
	$save( $post_id, $elements, 'elementor_canvas' );
	return $post_id;
};
$page_key = 'header';
$template(
	'Header',
	'type_header',
	array(
		$box(
			array( 'flex_direction' => 'row', 'flex_justify_content' => 'space-between', 'flex_align_items' => 'center', 'padding' => $pad( 15 ),
				'background_background' => 'classic', 'background_color' => '#FFFFFF' ),
			array(
				$widget( 'hfe-site-title', array( 'heading_link' => array( 'url' => '' ), 'size' => 'default', 'heading_tag' => 'h2' ) ),
				$widget( 'navigation-menu', array( 'menu' => 'main-menu', 'layout' => 'horizontal', 'align_items' => 'right' ) ),
				$widget( 'button', array( 'text' => $phone, 'link' => $tel, 'selected_icon' => array( 'value' => 'fas fa-phone', 'library' => 'fa-solid' ), 'background_color' => $teal ) ),
			)
		),
	)
);
$page_key = 'footer';
$template(
	'Footer',
	'type_footer',
	array(
		$box(
			array( 'flex_direction' => 'row', 'flex_justify_content' => 'space-between', 'padding' => $pad( 40 ), 'background_background' => 'classic', 'background_color' => $navy ),
			array(
				$p( "<p><span style=\"color: #ffffff;\"><strong>Harbour Plumbing and Heating</strong><br />Unit 3, Harbour Road Industrial Estate, Portwen, Cornwall<br />Phone: $phone</span></p>" ),
				$p( '<p><span style="color: #ffffff;">Gas Safe registered<br />Monday to Friday, 8am to 5pm</span></p>' ),
			)
		),
		$box(
			array( 'flex_direction' => 'row', 'padding' => $pad( 10 ), 'background_background' => 'classic', 'background_color' => '#0F2438' ),
			array( $widget( 'copyright', array( 'shortcode' => 'Copyright © [hfe_current_year] [hfe_site_title]', 'title_color' => '#FFFFFF' ) ) )
		),
	)
);

// The kit's colours and fonts (Site Settings), then Elementor's CSS for every page, as after a save in the editor.
$kit = Plugin::$instance->kits_manager->get_active_kit();
$kit->save( array( 'settings' => array_merge( $kit->get_settings(), array(
	'system_colors' => array(
		array( '_id' => 'primary', 'title' => 'Primary', 'color' => $navy ),
		array( '_id' => 'secondary', 'title' => 'Secondary', 'color' => $teal ),
		array( '_id' => 'text', 'title' => 'Text', 'color' => '#2B2B2B' ),
		array( '_id' => 'accent', 'title' => 'Accent', 'color' => '#F2A541' ),
	),
	'site_name' => 'Harbour Plumbing and Heating',
) ) ) );
Plugin::$instance->files_manager->clear_cache();
foreach ( get_posts( array( 'post_type' => array( 'page', 'elementor-hf', 'elementor_library' ), 'numberposts' => -1, 'post_status' => 'any', 'fields' => 'ids' ) ) as $pid ) {
	( new \Elementor\Core\Files\CSS\Post( $pid ) )->update();
}
WP_CLI::success( "Pages built: home $home, services $services, contact $contact, form $form_id" );
