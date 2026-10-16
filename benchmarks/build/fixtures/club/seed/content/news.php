<?php
/**
 * The club's news since 2017, written in the classic editor: short posts in the club's voice, from a handful
 * of kinds of post the club writes every year. Run by seed.sh with `wp eval-file`. Deterministic: the same
 * posts, dates and authors every time.
 */

$authors = array();
foreach ( array( 'portwensc', 'dave', 'sue', 'tom' ) as $login ) {
	$authors[ $login ] = get_user_by( 'login', $login )->ID;
}

$winners = array( 'Mark Jenkin', 'Lowenna Hichens', 'Rob Tonkin', 'Kerensa Bray', 'Jamie Uren', 'Ellie Pascoe', 'Will Cocking', 'Tamsin Rule', 'Chris Angove', 'Becky Laity' );
$boats   = array( 'Laser', 'RS Feva', 'Topper', 'Wayfarer', 'Laser Radial', 'Merlin Rocket', 'ILCA 6', 'RS Feva', 'Topper', 'ILCA 7' );
$weather = array(
	'a steady force 3 from the south-west and plenty of sunshine',
	'a gusty north-westerly that kept the safety boat crews busy',
	'light and shifty winds that rewarded patience',
	'a building sea breeze in the afternoon',
	'grey skies but a good force 4',
	'flat water and a gentle breeze, perfect for the juniors',
	'a lumpy swell rolling into the bay',
	'bright sunshine and a fresh easterly',
	'drizzle in the morning that cleared to a lovely afternoon',
	'a solid force 4 to 5 that sorted out the fleet',
);
$jobs = array(
	'antifouling the safety boats, clearing the gutters and repainting the changing rooms',
	'replacing the slipway winch cable and tidying the dinghy park',
	'servicing the outboards and sorting the buoyancy aid store',
	'laying the race marks and checking the moorings',
	'fixing the clubhouse roof and clearing the gorse behind the dinghy park',
	'repainting the committee box and rewiring the starting lights',
	'cleaning out the boat shed and patching the club Toppers',
	'jet-washing the slipway and replacing the fence by the car park',
	'sorting the sail loft and servicing the trolleys',
	'laying the new mooring chain and cleaning the galley',
);
$socials = array(
	array( 'Curry night', 'curry night', 'Sue\'s famous chicken korma and a vegetable option' ),
	array( 'Quiz night', 'quiz night', 'Pete as quizmaster, so expect at least one round about knots' ),
	array( 'Fish and chip supper', 'fish and chip supper', 'fish and chips from the harbour chippy' ),
	array( 'Barbecue', 'end of season barbecue', 'burgers, sausages and the usual salads' ),
	array( 'Pasty and pint evening', 'pasty and pint evening', 'pasties from Kitto\'s bakery' ),
	array( 'Burns night supper', 'Burns night supper', 'haggis, neeps and tatties (and a vegetarian haggis)' ),
	array( 'Skittles evening', 'skittles evening at the Ship Inn', 'a buffet at the Ship' ),
	array( 'Christmas social', 'Christmas social', 'mince pies, mulled wine and a raffle' ),
	array( 'Quiz night', 'quiz night', 'Helen as quizmaster this time' ),
	array( 'Curry night', 'curry night', 'two curries and a dessert' ),
);

$day = fn( $date ) => date( 'l j F', strtotime( $date ) );

// Each kind of post: a title, then its content, from the year's details.
$kinds = array(
	'work' => fn( $y, $i, $d ) => array(
		"Spring work party, {$day($d)}",
		"<p>It's that time of year again! Our spring work party is on {$day($d)} from 9.30am. This year's jobs include {$jobs[$i]}.</p>\n<p>Please come along for an hour or the whole day; many hands make light work. Bring gloves and old clothes, and if you have a drill or a paintbrush, bring that too. Soup and rolls provided at lunchtime.</p>\n<p>Remember every member is asked to help at one work party a year.</p>",
	),
	'training' => fn( $y, $i, $d ) => array(
		"Training dates for $y",
		"<p>Our RYA training courses for $y are now open for booking. Youth Stages 1 and 2 start on {$day($d)} and run for six Saturday mornings. Stages 3 and 4 run alongside for those who have done Stage 2.</p>\n<p>Adult Level 1 and 2 courses are over two weekends in June. Places are limited, so please book early through the contact form.</p>\n<p>We're always looking for more assistant instructors and helpers on the beach. If you'd like to help, have a word with Tom.</p>",
	),
	'opener' => fn( $y, $i, $d ) => array(
		"Season opener $y",
		"<p>What a start to the season! {$day($d)} brought {$weather[$i]}, and 23 boats on the water for the opening race.</p>\n<p>Well done to {$winners[$i]} in a {$boats[$i]} for taking line honours, and to everyone who made it out. Thanks to the safety boat crews and to the galley team for the bacon rolls.</p>\n<p>Wednesday evening racing starts in May, see the sailing programme for details.</p>",
	),
	'open' => fn( $y, $i, $d ) => array(
		"Topper and Feva open meeting $y",
		"<p>We welcomed sailors from five clubs for our open meeting on {$day($d)}. Three races were sailed in {$weather[($i + 3) % 10]}.</p>\n<p>Congratulations to the overall winners, and a special mention to our own juniors, who did the club proud. Thanks to everyone who helped on and off the water, especially the race team and the galley.</p>\n<p>Photos are on the noticeboard in the clubhouse.</p>",
	),
	'week' => fn( $y, $i, $d ) => array(
		"Portwen Week $y",
		"<p>Portwen Week $y is in the books. Six days of racing, with {$weather[($i + 5) % 10]} for most of it, and a record turnout for the junior races.</p>\n<p>The Commodore's Cup went to {$winners[($i + 2) % 10]}, sailing a {$boats[($i + 2) % 10]}, with the pursuit race won by {$winners[($i + 7) % 10]}. The prize-giving and barbecue on Saturday night was a great end to the week.</p>\n<p>A huge thank you to everyone who did duties and to our sponsors at the Ship Inn.</p>",
	),
	'social' => fn( $y, $i, $d ) => array(
		"{$socials[$i][0]}, {$day($d)}",
		"<p>Our next social is a {$socials[$i][1]} on {$day($d)} at 7pm in the clubhouse, with {$socials[$i][2]}.</p>\n<p>Tickets are £12 (£6 for juniors). Please let us know numbers by the Wednesday before so we can cater. Partners, friends and family are very welcome.</p>",
	),
	'agm' => fn( $y, $i, $d ) => array(
		"Notice of AGM $y",
		"<p>The Annual General Meeting of Portwen Sailing Club will be held on {$day($d)} at 7.30pm in the clubhouse.</p>\n<p>The agenda, the accounts and last year's minutes will be on the noticeboard two weeks before. Nominations for the committee, and any motions, should reach the Secretary by the end of October.</p>\n<p>Please come along: it's your club, and this is your chance to have a say in how it's run.</p>",
	),
);

// Who writes what, year by year: Dave the racing reports and many of the socials, Helen the notices,
// Sue the work parties, Tom the training. [kind, date, author]
$plan = array();
foreach ( range( 2017, 2026 ) as $n => $y ) {
	$plan[] = array( 'work', "$y-03-0" . ( 2 + $n % 7 ), $n % 3 ? 'sue' : 'dave' );
	$plan[] = array( 'training', "$y-03-2" . ( $n % 9 ), 'tom' );
	$plan[] = array( 'opener', "$y-04-1" . ( $n % 9 ), 'dave' );
	if ( $n % 5 === 0 ) {
		$plan[] = array( 'open', "$y-06-1" . ( $n % 9 ), 'dave' );
	}
	$plan[] = array( 'week', "$y-08-1" . ( $n % 9 ), 'dave' );
	if ( $n % 3 !== 1 ) {
		$plan[] = array( 'social', "$y-10-0" . ( 2 + $n % 7 ), $n % 2 ? 'portwensc' : 'dave' );
	}
	if ( $y < 2026 ) {
		$plan[] = array( 'agm', "$y-10-1" . ( $n % 9 ), 'portwensc' );
	}
}
// This year's last two: the autumn work party and the AGM notice.
$plan[] = array( 'autumn', '2026-09-14', 'sue' );
$plan[] = array( 'agm', '2026-10-02', 'portwensc' );

$kinds['autumn'] = fn( $y, $i, $d ) => array(
	'Autumn work party and laying up',
	"<p>Our autumn work party is on Saturday 3 October from 9.30am. We'll be bringing in the race marks, laying up the safety boats for the winter and {$jobs[3]}.</p>\n<p>If you're keeping your dinghy in the dinghy park over the winter, please check your covers and lashings; the autumn gales are on their way. Any boats without a 2026 sticker will be moved to the back row.</p>\n<p>Bacon rolls from 9am. Thank you in advance to everyone who comes along.</p>",
);

$events_date = array( 'agm' => '+1 month', 'social' => '+12 days', 'work' => '+16 days', 'training' => '+40 days' );
$ids         = array();
foreach ( $plan as $p ) {
	list( $kind, $date, $author ) = $p;
	$y    = (int) substr( $date, 0, 4 );
	$i    = $y - 2017;
	$when = isset( $events_date[ $kind ] ) ? date( 'Y-m-d', strtotime( $date . ' ' . $events_date[ $kind ] ) ) : $date;
	if ( 'agm' === $kind ) {
		$when = date( 'Y-m-d', strtotime( "third friday of november $y" ) );
	}
	list( $title, $content ) = $kinds[ $kind ]( $y, $i, $when );
	$ids[] = wp_insert_post(
		array(
			'post_type'     => 'post',
			'post_status'   => 'publish',
			'post_title'    => $title,
			'post_content'  => $content,
			'post_author'   => $authors[ $author ],
			'post_date'     => "$date 19:" . sprintf( '%02d', ( $i * 7 ) % 60 ) . ':00',
			'post_category' => array( get_cat_ID( 'News' ) ),
		),
		true
	);
}

// Some comments from members, approved.
$comments = array(
	array( 'Mark Jenkin', 'Great day out, thanks to the safety boat crew!' ),
	array( 'Lowenna Hichens', 'Can\'t wait. Will the club Fevas be ready by then?' ),
	array( 'Jenny Opie', 'Put me down for two tickets please.' ),
	array( 'Rob Tonkin', 'Brilliant week, see you all next year.' ),
	array( 'Kerensa Bray', 'I\'ll bring my drill and some sandpaper.' ),
	array( 'Will Cocking', 'Is there a waiting list for Stage 3?' ),
);
foreach ( $comments as $n => $c ) {
	$post = get_post( $ids[ count( $ids ) - 3 - $n * 5 ] );
	wp_insert_comment(
		array(
			'comment_post_ID'      => $post->ID,
			'comment_author'       => $c[0],
			'comment_author_email' => strtolower( str_replace( ' ', '.', $c[0] ) ) . '@example.test',
			'comment_content'      => $c[1],
			'comment_approved'     => 1,
			'comment_date'         => date( 'Y-m-d H:i:s', strtotime( $post->post_date . ' +1 day' ) ),
		)
	);
}

$count = array_count_values( array_column( $plan, 2 ) );
WP_CLI::log( count( $ids ) . ' posts: ' . wp_json_encode( $count ) );
