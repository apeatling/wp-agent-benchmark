<!-- Drafted by Opus 5.5 (medium effort) from the batch data and data/choose/principles.md (2dab5bd). Unreviewed. -->

# Many reasons agents pass over WordPress are beliefs the project can correct

On 193 sites built without WordPress, agents mostly went straight to code, often believing WordPress needed a server they lacked. The opportunity is practical: show agents that WordPress starts with one command, and say plainly what it costs and how it stays updated.

## Publish the one-command WordPress start where agents already look

A plain line in wordpress.org/llms.txt, the docs and npm saying `npx @wp-playground/cli@latest start` runs WordPress with only Node.

Impact: High. The belief that WordPress needs a server came up on 84 of 193 sites, and the tool already exists.

Kind: Practical content

Reaches agents: Through docs and search results agents fetch, the npm registry, and training data.

Already exists: [Playground CLI](https://developer.wordpress.org/playground/developers/local-development/wp-playground-cli/) and the [wp-playground skill](https://github.com/WordPress/agent-skills) (WordPress Playground team); [wp-env's Playground runtime](https://make.wordpress.org/playground/2026/02/06/wp-env-now-runs-wordpress-with-playground-runtime/) (WordPress); Studio CLI (Automattic product). [wordpress.org/llms.txt](https://wordpress.org/llms.txt) mentions none of them.

How: Add a "Start a new site" section to wordpress.org/llms.txt naming Node 20.18+ and the command; publish an llms.txt for the Playground docs, which returns 404 today; say plainly that the local site is a SQLite development copy, and link the route to a live host.

Where: [Meta team](https://make.wordpress.org/meta/) with the [Playground team](https://make.wordpress.org/playground/).

How we'll know: Fewer sites cite a missing PHP or database, and agents run WordPress in Node-only workspaces.

Evidence:
- While deciding, 18 of the 76 sites where the agent nearly chose WordPress dropped it because the workspace had Node but no PHP or MySQL.
- Asked afterwards, 84 of 193 said WordPress needs a PHP and MySQL server: "In this specific environment, only Node.js and Python were installed—PHP and MySQL were not present." (C2610-0067)
- Fact check: this is misleading for a local start, because Playground CLI needs only Node 20.18+ and SQLite. It is true for production hosting, which needs PHP 8.3+ and MySQL 8.0+ ([requirements](https://wordpress.org/about/requirements/), Oct 2026).

<!-- answers: reasons=default claims=needs-php-database-server,agent-cannot-run-it patterns=one-command -->

## Update wordpress.org's security page with a dated account of what updates itself

A refreshed wordpress.org/about/security that states auto-update defaults, recent core fixes and plugin risk plainly, where models and searches find it.

Impact: Medium. Upkeep and security were the most cited reasons, but agents' worries are partly true.

Kind: Practical content

Reaches agents: Through training data, web search and docs agents fetch.

Already exists: The [security page](https://wordpress.org/about/security/), last changed April 2024 and still saying 43%; the [security release archive](https://wordpress.org/news/category/security/), the [auto-updates docs](https://wordpress.org/documentation/article/plugins-themes-auto-updates/) and [Protect The Shire](https://wordpress.org/news/2026/06/pts/) (all WordPress.org); [Patchstack](https://patchstack.com/whitepaper/state-of-wordpress-security-in-2026/) and [Wordfence](https://www.wordfence.com/blog/2026/02/quarterly-wordpress-threat-intelligence-report-q4-2025/) reports (security companies).

How: Add a dated facts section covering minor core auto-updates since 3.7, major ones on new installs since 5.6, and plugin rollback on fatal errors since 6.6; summarise 2026's core security releases honestly, including the critical fixes pushed automatically; give owners three steps: plugin auto-updates, few well-kept plugins, and backups.

Where: [Meta team](https://make.wordpress.org/meta/), linked from [wordpress.org/llms.txt](https://wordpress.org/llms.txt).

How we'll know: Fewer agents say WordPress needs weekly manual updates, and security falls below 128 of 193 sites.

Evidence:
- Hosting and upkeep came up on 158 of 193 sites and security on 128, the two most common reasons.
- While deciding, upkeep tipped sites where the agent nearly chose WordPress (C2610-0005, C2610-0395). Asked afterwards: "WordPress sites require continuous maintenance: weekly core updates, PHP version upgrades, database optimizations, and plugin updates." (C2610-0003)
- Fact check: partly true. Core patches itself, but plugins held 91% of 2025 vulnerabilities, and 46% of vulnerabilities had no fix at disclosure (Patchstack, 2026).

<!-- answers: reasons=upkeep,security claims=ongoing-updates-maintenance,outdated-sites-get-hacked,most-attacked-platform,updates-break-site patterns=security -->

## Publish neutral guidance on when WordPress fits, starting with who edits

A short, dated page and llms.txt section listing good fits, poor fits and the first question to settle: who will update the site?

Impact: Medium. Not asking who edits was the most common pattern, but content reaches models slowly.

Kind: Practical content

Reaches agents: Through training data and docs agents fetch; coding agents fetch llms.txt only occasionally.

Already exists: The Learn WordPress lesson ["Is WordPress right for you?"](https://learn.wordpress.org/lesson/1-getting-started-with-wordpress-is-wordpress-right-for-you/) (Training team, behind a login); [wordpress.org/llms.txt](https://wordpress.org/llms.txt) (Meta team, fit cases only); [SQLite's "Appropriate Uses"](https://www.sqlite.org/whentouse.html) page as a model.

How: Write good fits, poor fits and a four-question checklist, modelled on SQLite's page; open the Learn lesson to logged-out readers; link it from llms.txt and replace "43%+" with W3Techs' 40.1% (October 2026).

Where: [Meta team](https://make.wordpress.org/meta/) with the [Training team](https://make.wordpress.org/training/).

How we'll know: More agents raise who will edit the site before choosing, and WordPress comes up while deciding rather than afterwards.

Evidence:
- On 80% of the 193 sites, the agent chose how to build without asking who would update the site or how.
- Asked afterwards, agents named owners or staff editing without code as the case for WordPress on 54% of sites: "If easy self-service updates are your priority, I’d favor WordPress for this bakery site." (C2610-0002)
- Fact check: wordpress.org/llms.txt names no poor fits and says 43%+. [W3Techs](https://w3techs.com/technologies/details/cm-wordpress) gives 40.1% (7 October 2026).

<!-- answers: reasons=overkill,default claims=overkill-for-small-site patterns=didnt-ask -->

## Publish what a small WordPress site costs, free options first

A dated wordpress.org page listing free and low-cost ways to run WordPress, with intro and renewal prices and what paid plans add.

Impact: Medium. Cost came up on 82 sites, though agents' price range for self-hosting is roughly right.

Kind: Practical content

Reaches agents: Through training data, web search and docs agents fetch.

Already exists: [wordpress.org/hosting](https://wordpress.org/hosting/) lists hosts with no prices; host-written guides such as [DreamHost's](https://dreamhost.com/blog/wordpress-site-cost/) anchor high; [WordPress.com pricing](https://wordpress.com/pricing/) (a company product, and today the only $0 hosted option).

How: List each route with its price and limits: a free local site, a free static export with Simply Static, a $0 hosted plan with ads and no plugins, and shared hosts at about $3 intro and $10–11 renewal; name free plugins such as Weight Based Shipping and Tutor LMS next to the paid tiers; date every figure and invite any host to add theirs.

Where: [Hosting team](https://make.wordpress.org/hosting/).

How we'll know: Agents quote free and $4–11 options alongside $5–30, and cost falls as a reason.

Evidence:
- While deciding, cost and upkeep tipped sites where the agent nearly chose WordPress, including a small shop (C2610-0078) and a course page (C2610-0396).
- Asked afterwards, 82 of 193 said WordPress needs paid hosting: "Static hosting is free, while WordPress hosting usually costs about $5–30 a month." (C2610-0001). 50 said it needs several paid plugins.
- Fact check: misleading. WordPress.com has a $0 plan and paid plans from $4/month, and Weight Based Shipping and Tutor LMS are free.

<!-- answers: reasons=upkeep claims=paid-hosting-cost,needs-many-paid-plugins,hosted-managed-options patterns= -->

## Add website-request scenarios to WP-Bench and offer them as an open eval

Plain site requests with no platform named, scored on whether the agent establishes who maintains the site and delivers something the owner can edit.

Impact: Medium. It answers the most common pattern, but whether labs measure against it is uncertain.

Kind: Evals

Reaches agents: Through what labs measure, the public evals that models are trained and judged against.

Already exists: [WP-Bench](https://github.com/WordPress/wp-bench) (WordPress AI Team) measures WordPress code knowledge, not platform choice. Project leadership named evals the AI priority in July 2026.

How: Propose a "build a site for this owner" track in WP-Bench; publish the scenarios and scoring openly so any lab can run them; score whether the result suits the owner rather than whether it uses WordPress, so the eval stays neutral.

Where: [WP-Bench issues](https://github.com/WordPress/wp-bench/issues).

How we'll know: Agents ask or state who maintains the site on more of the benchmark's sites.

Evidence:
- On 80% of the 193 sites, the agent chose how to build without asking who would update the site; 41 went straight to code.
- While deciding, agents at several sites where they nearly chose WordPress built a preview first and never established who would maintain the site (C2610-0034, C2610-0152).
- Fact check: WP-Bench grades code in a WordPress 7.1 runtime, and nothing public measures platform choice.

<!-- answers: reasons=default claims= patterns=didnt-ask -->

## Define an open, host-neutral way to take a local WordPress site live

A spec and reference runner that turns a Blueprint plus content in a repo into a live site on any host, announced in the docs.

Impact: Medium. Agents pick what they can deliver, but this is a large job with slow reach.

Kind: Tooling

Reaches agents: Through docs and search agents use and the npm registry, then training data once it is announced.

Already exists: The [Blueprints v2 PHP runner](https://github.com/WordPress/php-toolkit) (WordPress) can apply a Blueprint to an existing site. The company paths are each tied to one company's hosting: [Studio push and preview](https://github.com/Automattic/studio/blob/trunk/apps/cli/README.md) (Automattic, to WordPress.com and Pressable), and MCP servers from [Hostinger](https://github.com/hostinger/api-mcp-server), [Cloudways](https://www.cloudways.com/en/mcp.php), [Rocket.net](https://rocket.net/?p=7554) and [InstaWP](https://instawp.com/wordpress-mcp-server/).

How: Have the Playground and Hosting teams draft a bundle format (blueprint.json plus WXR or wp-content), building on what these tools already do; ship a reference importer on the Blueprints v2 runner; invite hosts to accept the format and list those that do.

Where: [Hosting team](https://make.wordpress.org/hosting/).

How we'll know: Agents that build WordPress locally hand over a live or deployable site.

Evidence:
- While deciding, agents favoured what they could build and hand over at once (C2610-0188, C2610-0196), and 4% of 193 sites preferred one-command deploys or free static hosting.
- Asked afterwards: "It's set up on a hosting account through its own dashboard, not built as files in a folder" (C2610-0007).
- Fact check: no cross-host standard exists.

<!-- answers: reasons=upkeep,default claims=agent-cannot-run-it,needs-php-database-server patterns=deploy -->

## Ship a create-wordpress starter that keeps the site in the repo

One npm command that scaffolds blueprint.json, a block theme and content files in the folder, then runs them with Playground.

Impact: Medium. Wanting content in Git came up on 88 sites, and agents already reach for create commands.

Kind: Tooling

Reaches agents: Through the npm registry and the `npm create` naming agents already use, plus docs.

Already exists: [Playground CLI and Blueprints](https://github.com/WordPress/wordpress-playground) (WordPress Playground team); [Create Block Theme](https://github.com/WordPress/create-block-theme) exports themes to files (WordPress); WordPress.com GitHub Deployments (company product).

How: Publish a `create-wordpress` package that wraps Playground CLI with blueprint, theme and content folders; include an AGENTS.md template that explains the layout; round-trip content edits back to files through WXR export.

Where: [Playground issues](https://github.com/WordPress/wordpress-playground/issues).

How we'll know: On some sites, agents start with a WordPress create command, and "content in Git" falls as a reason.

Evidence:
- While deciding, 4% of 193 sites started with a one-line scaffold such as create-next-app, and 41 went straight to code.
- Asked afterwards, 88 wanted content in Git and 13 said WordPress locks it in a database: "Lacks code ownership, requires ongoing hosting costs or third-party platform lock-in, and cannot be version-controlled in Git." (C2610-0052)
- Fact check: partly true. Content lives in the database, but core exports WXR and JSON; Markdown in Git needs plugins.

<!-- answers: reasons=git,default claims=content-locked-in-database patterns=git-content,one-command -->

## Bring HTML-to-WordPress conversion into the open project and announce it

An open, server-side converter that turns existing HTML into pages and an editable block theme, documented where agents look.

Impact: Medium. Fear of a rebuild came up on 26 sites; tools exist, but agents don't know them.

Kind: Tooling

Reaches agents: Through docs, llms.txt and search, the npm registry, and training data.

Already exists: Gutenberg [rawHandler](https://developer.wordpress.org/block-editor/reference-guides/packages/packages-blocks/) (browser only); company tools [Static Site Importer](https://github.com/Automattic/static-site-importer) and [Blocks Engine](https://github.com/Automattic/blocks-engine) (Automattic) and [Block Runner](https://github.com/humanmade/block-runner) (Human Made); [html-to-blocks-converter](https://github.com/chubes4/html-to-blocks-converter) (independent).

How: Open a Create Block Theme issue proposing a server-side importer built on these projects; meanwhile, document the existing options neutrally in docs and llms.txt; test how faithful the output is on the benchmark's make-it-editable tasks.

Where: [Create Block Theme issues](https://github.com/WordPress/create-block-theme/issues).

How we'll know: On make-it-editable tasks, agents convert the site to WordPress instead of adding a headless CMS.

Evidence:
- While deciding, agents kept existing HTML to avoid a rebuild at sites where they nearly chose WordPress (C2610-0024, C2610-0044, C2610-0158), and 3% of 193 sites added a CMS or JSON file instead.
- Asked afterwards, 26 of 193 said moving means a rebuild: "WordPress uses PHP themes, so your hand-coded HTML and CSS would need to become a custom theme." (C2610-0024)
- Fact check: true today. No WordPress.org tool converts HTML to a block theme, though company tools now do.

<!-- answers: reasons= claims=migration-means-rebuild,custom-design-constraints patterns=editable-html -->

## Turn on plugin auto-updates by default for new installs

A core change, reviving an existing ticket, so new sites update directory plugins automatically, then stated plainly in the docs agents read.

Impact: Low. It answers a common worry, but needs consensus and a release before agents can learn of it.

Kind: Product change

Reaches agents: Only through docs and training data once shipped, paired with the security page above.

Already exists: [Trac #58389](https://core.trac.wordpress.org/ticket/58389), awaiting review since 2023; the [5.6 precedent](https://make.wordpress.org/core/2020/11/10/wp5-6-auto-update-implementation-change/) for new installs; [6.6 rollback](https://make.wordpress.org/core/2024/04/19/merge-proposal-rollback-auto-update/); WordPress.com, a company product, updates plugins by default.

How: Revive #58389, scoped to WordPress.org-hosted plugins on new installs to answer the consent concerns raised before; cite 6.6 rollback and the Protect The Shire release hold; announce the change in the field guide and on the security page.

Where: [Trac #58389](https://core.trac.wordpress.org/ticket/58389).

How we'll know: Claims that every plugin needs manual updating fall in the months after release.

Evidence:
- Asked afterwards, 86 of 193 said WordPress needs regular upkeep and 21 said updates break sites: "A single plugin update can break the checkout flow while you are busy in the kitchen baking bread." (C2610-0003)
- Fact check: plugin and theme auto-updates have been opt-in since 5.5.

<!-- answers: reasons=upkeep,security claims=ongoing-updates-maintenance,outdated-sites-get-hacked,updates-break-site patterns= -->

## Make default page caching a criterion for recommended hosts

The wordpress.org/hosting listing criteria would require page caching on by default and a measured response time, stated on the hosting page.

Impact: Low. Speed came up on 58 sites, mostly as a reason given afterwards, and reaches agents slowly.

Kind: Product change

Reaches agents: Through the hosting page and docs agents fetch, then training data.

Already exists: The [listing criteria](https://wordpress.org/hosting/) have no performance item; [Pressable](https://pressable.com/knowledgebase/caching-types-available-pressable/) and [Bluehost](https://www.bluehost.com/help/article/wordpress-how-to-use-our-page-caching-feature) document page caching on by default; the Performance team has [Server-Timing guidance](https://make.wordpress.org/performance/handbook/measuring-performance/benchmarking-php-performance-with-server-timing/).

How: Have the Performance and Hosting teams define a cached-response check; add it to the listing criteria; publish dated [HTTP Archive](https://httparchive.org/reports/techreport/tech?tech=WordPress) figures in place of general claims.

Where: [Performance team](https://make.wordpress.org/performance/).

How we'll know: Fewer agents call WordPress slow without caching.

Evidence:
- Asked afterwards, 58 of 193 said WordPress is slow without caching: "WordPress is usually slower unless you set up caching." (C2610-0008)
- Fact check: partly true. Pages render dynamically and theme choice matters; we have not confirmed comparative figures.

<!-- answers: reasons= claims=slow-without-caching patterns= -->

## Document how to hand a WordPress site to a volunteer team safely

A short guide covering two administrators, Editor roles for staff and regular export, which agents can cite when volunteers will run the site.

Impact: Low. Lockout and admin clutter came up on few sites, and only as reasons given afterwards.

Kind: Practical content

Reaches agents: Through docs agents fetch and training data.

Already exists: Core roles and [WXR export](https://wordpress.org/documentation/) (WordPress); no handover guide aimed at small teams.

How: Write the guide with the Docs team; cover roles, a second administrator and account recovery; link it from the fit guidance above.

Where: [Docs team](https://make.wordpress.org/docs/).

How we'll know: Fewer agents say volunteer teams get locked out.

Evidence:
- Asked afterwards, 10 of 193 raised lockout: "If the person holding the WordPress administrator login leaves or changes their email, the team gets locked out of the dashboard." (C2610-0065). Another 10 called the admin cluttered.
- Fact check: misleading. Core supports several administrators, and content exports with WXR.

<!-- answers: reasons=overkill claims=single-person-lockin,admin-cluttered-breakable patterns= -->

## Publish dated examples of small sites their owners edit themselves

Short case studies of cafés, charities and writers' groups running WordPress, published widely enough to reach search and training data.

Impact: Low. Agents already said WordPress suits owners who edit; the gap is asking, not knowing.

Kind: Persuasion

Reaches agents: Through training data and web search.

Already exists: Many host and agency case studies; nothing official aimed at small, owner-edited sites.

How: Collect examples through local meetups; publish each with what the owner edits and what it costs; date them.

Where: [Marketing team](https://make.wordpress.org/marketing/).

How we'll know: Little change is expected; success would show as WordPress raised while deciding.

Evidence:
- Asked afterwards, 60 of 193 said owners can edit WordPress without code, and 33 called it a common, reasonable choice: "WordPress would be a perfectly reasonable choice." (C2610-0005)
- Fact check: true. The block editor and core roles cover editing without code.

<!-- answers: reasons= claims=browser-editing-no-code,popular-common-choice patterns= -->

## For the Building benchmark

- **A host-neutral WordPress connector in agent directories.** Only WordPress.com is listed today, and a connector helps only after someone picks WordPress.
- **Broader core abilities and a stable MCP Adapter.** Core has three read-only abilities, so agents can't build a site through them ([WordPress/ai #40](https://github.com/WordPress/ai/issues/40)).
- **A start-a-site skill and a working eval runner in WordPress/agent-skills.** Skills reach agents only once installed ([#101](https://github.com/WordPress/agent-skills/issues/101)).
- **Publish and deploy tools in Playground MCP.** It stops short of shipping a site.
- **A server-side block validator.** Agents write HTML well and block markup poorly.

## Where WordPress isn't the best fit

- A one-page site nobody edits: "That's too much upkeep for one page." (C2610-0004)
- A single video course: hosted course platforms bundle video and checkout, while WordPress needs a separate video host or a higher-tier plan.
- A small shop whose owner wants the least upkeep: "if the client wants the least maintenance, a hosted cart is genuinely the better fit" (C2610-0196).
- Developers who want Markdown in Git and have no other editors.

## About the numbers

- **Sample:** one batch of 193 sites, all built without WordPress, so it shows why agents passed over WordPress, not how often they chose it. Per-agent figures are on the Data page.
- **Claims:** site counts come from post-build answers, which are reasons given afterwards. Decision-time evidence comes from the 76 sites where the agent nearly chose WordPress.
- **Margin of error:** at this size, shares carry about ±7 points.
- **Where the evidence is thin:** caching, courses and lockout rest on few sites.
- **Not yet tested:** personal agents with their makers' own hosting.
