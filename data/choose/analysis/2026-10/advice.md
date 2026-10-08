<!-- Drafted by Opus 5.5 (high effort) from the batch data and data/choose/principles.md (701d5f1). Unreviewed. -->

# Agents see where WordPress fits, but decide before they ask

Agents built 193 sites without WordPress. Many named it the better fit only after building, and they cited costs and upkeep that are often overstated. Guidance agents read before they build, and WordPress sites that start and travel like files, would win more of those choices.

## Publish guidance agents read before choosing how to build a site

Agents skip the one question, who edits the site, that most often points to WordPress.

Evidence:
- 80% of the 193 sites: the agent chose how to build without asking who would update the site or how they wanted to edit it.
- 54% of the 193 sites: the agent said WordPress would fit if the owner, staff or volunteers want to edit in a browser without code. No condition came up more often. The question agents skip is the one that decides for WordPress.
- "More than the site needs" was a reason the agent passed on WordPress at 70% of sites (136 of 193). "Went straight to code" was a reason at 21% (41 of 193).
- "If easy self-service updates are your priority, I’d favor WordPress for this bakery site." (C2610-0002)
- Fact check, 7 Oct 2026:
  - [wordpress.org/llms.txt](https://wordpress.org/llms.txt) describes WordPress but offers no questions for deciding and names no poor fits.
  - It says "more than 43%", where [W3Techs](https://w3techs.com/technologies/details/cm-wordpress) shows 40.1%.
  - The [Learn WordPress lesson on fit](https://learn.wordpress.org/lesson/1-getting-started-with-wordpress-is-wordpress-right-for-you/) needs a login.
  - None of the 19 [official agent skills](https://github.com/WordPress/agent-skills) helps decide. All of them assume a WordPress codebase already exists.

Ways to help:
- Add fit questions and poor fits to the official llms.txt
  Scale: Update
  Why: Agents already know when WordPress fits but apply it after building: "WordPress is great when you're adding content often, like blog posts, lots of pages or several people editing." (C2610-0004)
  Already exists: Markdown versions of wordpress.org pages and llms.txt, from the Meta team ([March 2026](https://make.wordpress.org/meta/2026/03/03/markdown-now-available-on-wordpress-org/)). SQLite's [Appropriate Uses](https://www.sqlite.org/whentouse.html) page is a model for listing fits, poor fits and a short checklist.
  How: Add a "choosing a platform" section with three questions (who edits, how often, which features); list where another option fits better; date the market-share figure.
  Where: [make.wordpress.org/meta](https://make.wordpress.org/meta/)
  How we'll know: WordPress comes up while agents decide, not only afterwards. "More than the site needs" falls below 70% by more than the margin.
- Add a platform-choice skill that triggers on website requests
  Scale: Extend
  Why: At C2610-0046, -0048 and -0092 the agent recommended WordPress only after it had finished building.
  Already exists: [WordPress/agent-skills](https://github.com/WordPress/agent-skills) (open project) requires evals, and its router assumes WordPress has already been chosen. Automattic's [WordPress Site Creator](https://github.com/Automattic/wordpress-agent-skills) (company product, stalled) gathers a site specification but doesn't ask who edits.
  How: Open a scope issue first; describe the skill as "choosing how to build a website" so it loads before any platform is picked; ship it with an eval and list it in skills directories.
  Where: [agent-skills issues](https://github.com/WordPress/agent-skills/issues)
  How we'll know: In test runs with the skill installed, agents ask or state who will edit before building. Also track whether it loads at all: [Vercel found](https://vercel.com/blog/agents-md-outperforms-skills-in-our-agent-evals) a skill went unused in 56% of its eval cases.
- Add website-choice tasks to the official WordPress AI benchmark
  Scale: Extend
  Why: Nothing official measures whether agents weigh who will run a site. Leadership named evals as the AI priority in [July 2026](https://make.wordpress.org/core/2026/06/22/merge-proposal-guidelines-built-on-knowledge/).
  Already exists: [WP-Bench](https://github.com/WordPress/wp-bench) (open project) tests WordPress code knowledge only. This benchmark's plain website requests could supply the tasks.
  How: Propose a task set drawn from these requests; score whether the agent checks who edits and names when WordPress fits; publish the tasks so any agent maker can run them.
  Where: [WP-Bench issues](https://github.com/WordPress/wp-bench/issues)
  How we'll know: The share of sites built without asking who updates them falls below 80% by more than the margin.

<!-- answers: scale=update reasons=overkill,default claims=overkill-for-small-site conditions=self-edit-without-code,multiple-editors,regular-blogging,already-uses-wordpress patterns=didnt-ask -->

## Correct the cost, upkeep and security facts agents repeat

The reasons agents give most for passing on WordPress are often outdated or overstated.

Evidence:
- "Hosting and upkeep" was a reason at 82% of sites (158 of 193). "Security and updates" was a reason at 66% (128 of 193). These are the top two reasons, so correcting them reaches the most decisions.
- 82 of the 193 sites (42%): the agent said WordPress needs paid hosting, usually "$5–30 a month". Checked: misleading.
  - WordPress.com, a company product, has a $0 plan (ads, a subdomain, no plugins) and paid plans from $4 a month billed yearly.
  - Shared hosts start around $3 a month.
  - The Simply Static plugin exports a site to free static hosting.
- 86 of the 193 sites (45%): the agent said someone must keep WordPress updated. Partly true:
  - Core security releases have installed themselves since 3.7.
  - New sites also take major releases automatically since 5.6.
  - Plugin and theme auto-updates are one click but off by default.
- 50 of the 193 sites (26%): the agent said features need several paid plugins, which "require annual subscription fees ($100–$300/yr per plugin)" (C2610-0003). Checked: misleading. WooCommerce tracks stock without add-ons, and free plugins cover weight-based shipping and course sales.
- Security claims:
  - 59 of the 193 sites (31%): the agent said out-of-date sites get hacked. Checked: true.
  - 58 of the 193 sites (30%): the agent called WordPress the most attacked platform. Checked: partly true.
  - [Patchstack](https://patchstack.com/whitepaper/state-of-wordpress-security-in-2026/) puts 91% of 2025's vulnerabilities in plugins.
  - Core had critical fixes in 2026 ([7.0.2 and 7.1.2](https://wordpress.org/news/category/security/)), and both were pushed to sites automatically.
  - [wordpress.org/about/security](https://wordpress.org/about/security/) was last updated in April 2024 and still says 43%.

Ways to help:
- Refresh the security page with dated, current facts
  Scale: Update
  Why: Agents state the risk without explaining how fixes reach sites: "It's the most attacked website platform, mostly through outdated plugins." (C2610-0019)
  Already exists: from the open project, the security page and white paper, the [security release archive](https://wordpress.org/news/category/security/), and [Protect The Shire](https://wordpress.org/news/2026/06/pts/), which holds plugin releases for review before they auto-update. From companies, independent counts by Patchstack and [Wordfence](https://www.wordfence.com/blog/2026/02/quarterly-wordpress-threat-intelligence-report-q4-2025/).
  How: Add a dated summary of this year's core security releases and how they reached sites; state the auto-update defaults; link advice on choosing plugins and the independent reports.
  Where: [make.wordpress.org/meta](https://make.wordpress.org/meta/)
  How we'll know: Agents mention automatic security fixes when they discuss risk. "Security and updates" falls below 66% by more than the margin.
- Publish free and paid options for a small site, with renewal prices
  Scale: Update
  Why: Agents anchor high: "WordPress needs a server running all the time with a database. That usually means paid hosting (about $5–25 a month)" (C2610-0006).
  Already exists: [wordpress.org/hosting](https://wordpress.org/hosting/) lists hosts without prices. Host-written guides such as [DreamHost's](https://dreamhost.com/blog/wordpress-site-cost/) put a business site near $415 in its first year. [WordPress.com pricing](https://wordpress.com/pricing/) is a company page.
  How: Add a dated table of free, shared and managed options with both introductory and renewal prices; say what paid plans add (support, backups, staging, speed, plugins); list free plugins for common features.
  Where: [make.wordpress.org/hosting](https://make.wordpress.org/hosting/)
  How we'll know: Fewer than 42% of sites say WordPress needs paid hosting, and agents name a free option alongside paid ones.
- Revive making plugin auto-updates the default for new sites
  Scale: Extend
  Why: Agents see plugin upkeep as an ongoing chore: "someone has to handle hosting, backups, security, and updates to WordPress, WooCommerce and every plugin" (C2610-0009).
  Already exists: [Trac #58389](https://core.trac.wordpress.org/ticket/58389) proposes this for plugins installed from Add New. It has been awaiting review since 2023, and a core committer supported it in 2025. 5.6 set the same default for major core updates on new installs, and 6.6 rolls back a plugin auto-update that causes a fatal error.
  How: Comment on #58389 with these precedents; scope it to WordPress.org-hosted plugins on new sites; leave themes out until they get rollback.
  Where: [Trac #58389](https://core.trac.wordpress.org/ticket/58389)
  How we'll know: Agents describe plugin updates as automatic, and claims that someone must handle every update fall below 45%.

<!-- answers: scale=update reasons=upkeep,security claims=paid-hosting-cost,ongoing-updates-maintenance,needs-many-paid-plugins,outdated-sites-get-hacked,most-attacked-platform conditions=someone-will-maintain -->

## Show agents how to start or convert WordPress from any folder

Many agents dropped WordPress because they thought they couldn't run or convert it where they were.

Evidence:
- 84 of the 193 sites (44%): the agent said WordPress needs a PHP server and a MySQL database before any page exists. Partly true: production hosting does. Locally, [Playground CLI](https://developer.wordpress.org/playground/developers/local-development/wp-playground-cli/) runs WordPress with only Node.js 20.18+ and SQLite.
- 19 of the 193 sites (10%): the agent said it couldn't install or run WordPress where it was. Checked: misleading. "In this specific environment, only Node.js and Python were installed—PHP and MySQL were not present." (C2610-0067)
- 15 of the 76 sites where the agent came close to choosing WordPress: it stopped because the workspace had no PHP or database (for example C2610-0093, -0280, -0387).
- 26 of the 193 sites (13%): the agent said moving to WordPress means a rebuild. Checked: true for the open project. Today only company tools turn a static site into an editable block theme.
- "Went straight to code" was a reason at 21% of sites (41 of 193). "Preferred its usual stack" was a reason at 6% (11 of 193).
- Fact check, 7 Oct 2026: wordpress.org/llms.txt doesn't mention Playground, npx or Node.js, and the Playground docs have no llms.txt.

Ways to help:
- Add a Node-only quick start to the official llms.txt
  Scale: Update
  Why: Agents often had exactly what Playground needs: "This container environment came ready with Node.js and Python." (C2610-0076)
  Already exists: Playground CLI and the wp-playground and blueprint skills (open project). Studio CLI (Automattic) and InstaWP sandboxes (InstaWP) are company options for previews.
  How: Add `npx @wp-playground/cli@latest start` with its Node 20.18 requirement; explain that the site is stored outside the project folder, so agents should commit a blueprint.json; publish an llms.txt for the Playground docs.
  Where: [make.wordpress.org/playground](https://make.wordpress.org/playground/)
  How we'll know: Fewer than 10% of sites say the agent couldn't run WordPress, and agents build WordPress in workspaces that have only Node.
- Add a start-a-new-site skill to the official agent skills
  Scale: Extend
  Why: At 4% of the 193 sites the agent's first step was a one-line scaffold such as create-next-app. Agents know no WordPress equivalent.
  Already exists: [WordPress/agent-skills](https://github.com/WordPress/agent-skills) covers existing codebases only, and its eval harness checks only frontmatter ([#101](https://github.com/WordPress/agent-skills/issues/101)). Studio Code (Automattic) builds sites from nothing, but only for Automattic hosting.
  How: Open a scope issue; write a skill that goes from an empty folder to a running site through Playground and a blueprint; add an eval that actually runs it.
  Where: [agent-skills issues](https://github.com/WordPress/agent-skills/issues)
  How we'll know: Agents that load the skill finish with a running WordPress site in the workspace.
- Add static HTML import to a community-stewarded block theme tool
  Scale: Extend
  Why: "WordPress uses PHP themes, so your hand-coded HTML and CSS would need to become a custom theme." (C2610-0024)
  Already exists: [Static Site Importer](https://github.com/Automattic/static-site-importer) and Blocks Engine (Automattic, used by Studio's `create --from`) convert whole sites. [Block Runner](https://github.com/humanmade/block-runner) (Human Made) converts HTML into blocks but doesn't build themes. [Create Block Theme](https://github.com/WordPress/create-block-theme) (open project) has no import.
  How: Propose an import feature in Create Block Theme; reuse a GPL engine such as Blocks Engine or Block Runner; expose it as a WP-CLI command agents can run.
  Where: [Create Block Theme issues](https://github.com/WordPress/create-block-theme/issues)
  How we'll know: Asked to make a hand-coded site editable, agents convert it to WordPress. Today 3% of sites instead keep the HTML and add a headless CMS or JSON file.

<!-- answers: scale=extend reasons=default,stack claims=needs-php-database-server,agent-cannot-run-it,migration-means-rebuild patterns=one-command,editable-html -->

## Define a portable WordPress site that any host can deploy

Agents prefer sites they can keep in a folder and hand over; WordPress sites don't travel that way yet.

Evidence:
- "Wanted content in Git" was a reason at 46% of sites (88 of 193).
- 9% of the 193 sites: the agent kept content in Markdown or other files in the repository.
- 4% of the 193 sites: the agent preferred its choice because it deploys with one command or to free static hosting.
- 13 of the 193 sites (7%): the agent said WordPress locks content in a database. Checked: partly true. WXR export, `wp export` and the REST API move content out, but no standard bundle exists that a host can deploy.
- Fact check:
  - Playground and Studio sites deploy natively only to WordPress.com and Pressable, both Automattic.
  - Hostinger, Cloudways, Rocket.net, InstaWP and Pantheon each have their own agent tools.
  - The [Hosting team](https://make.wordpress.org/hosting/) has no shared deploy standard.

Ways to help:
- Document the Blueprints PHP runner as a host deploy engine
  Scale: Extend
  Why: The runner can already apply a blueprint to an existing site, but no host is known to offer it as a deploy target.
  Already exists: the Blueprints v2 runner in [WordPress/php-toolkit](https://github.com/WordPress/php-toolkit) (open project, beta). Studio push (Automattic) is one company's working path.
  How: Write a guide for hosts; add a WP-CLI command that applies a blueprint plus exported content; test it with at least two hosts.
  Where: [php-toolkit issues](https://github.com/WordPress/php-toolkit/issues)
  How we'll know: An agent takes one blueprint to two different hosts using the same steps.
- Draft a portable site format: blueprint, theme and content in one repo
  Scale: New idea
  Why: Agents count lack of version control against WordPress: "Lacks code ownership, requires ongoing hosting costs or third-party platform lock-in, and cannot be version-controlled in Git." (C2610-0052)
  Already exists: Blueprints, WXR and Create Block Theme export are the pieces. Nothing yet ties them into one bundle.
  How: Publish a draft spec for a blueprint.json, a theme folder and exported content; build export from Playground as the reference implementation; invite hosts and plugin makers to review.
  Where: [make.wordpress.org/playground](https://make.wordpress.org/playground/)
  How we'll know: Agents keep WordPress sites in the repo, and "Wanted content in Git" falls below 46% by more than the margin.
- Propose a shared deploy call that any host can implement
  Scale: New idea
  Why: At C2610-0085 the agent built a custom shop partly because a WordPress shop needs a server it couldn't set up from where it was.
  Already exists: each host's own agent API or MCP server (Hostinger, Cloudways, Rocket.net, InstaWP, Pantheon, Pressable, WordPress.com). There is no common standard.
  How: Invite hosts to agree on one "create site from bundle" call over MCP or REST; publish conformance tests; leave pricing and service for hosts to compete on.
  Where: [make.wordpress.org/hosting](https://make.wordpress.org/hosting/)
  How we'll know: Agents put a WordPress site live in one step and cite one-command deploys for WordPress as they do for static hosts.

<!-- answers: scale=new reasons=git claims=content-locked-in-database patterns=git-content,deploy -->

## Start an agent-focused guide to WordPress on wordpress.org

Correct facts about WordPress are scattered, sometimes stale, and not written for agents to use.

Evidence:
- 11 of the 25 claims agents made most often about WordPress were checked as misleading or only partly true. They include the three most repeated claims, each made at 42–45% of the 193 sites.
- The facts that correct them sit on separate pages:
  - a security page last updated in 2024
  - a hosting page with no prices
  - a fit lesson behind a login
  - an llms.txt that describes WordPress rather than guiding the choice
- Only WordPress.com, not WordPress in general, is listed in [Claude's connector directory](https://claude.com/connectors/wordpress-com).
- Evidence is thin here. Nothing yet shows a guide changes agent choices. [Ahrefs](https://ahrefs.com/blog/llmstxt-study/) found 97% of llms.txt files got no requests in May 2026, though Claude Code was the second-largest AI fetcher.

Ways to help:
- Launch an agent guide on wordpress.org with dated, sourced facts
  Scale: New idea
  Why: Agents repeat price figures with no date or source: "Static hosting is free, while WordPress hosting usually costs about $5–30 a month." (C2610-0001)
  Already exists: Markdown versions of wordpress.org pages and llms.txt (Meta team), plus this benchmark's monthly fact checks.
  How: Start with five pages (when WordPress fits, cost, security, starting a site, handing it over); date every figure and refresh monthly; serve the pages as Markdown and index them from llms.txt.
  Where: [make.wordpress.org/meta](https://make.wordpress.org/meta/)
  How we'll know: Claims checked as misleading become less common by more than the margin, starting with paid hosting at 42%.
- Open a host-neutral directory of hosts' agent connectors
  Scale: New idea
  Why: Agents that can't reach a host hand over instructions instead of sites: "WordPress needs a hosting account running it, so I'd only be able to give you instructions, not a finished site." (C2610-0004)
  Already exists: agent tools from Hostinger, Cloudways, Rocket.net, InstaWP, Pantheon, GoDaddy and WordPress.com (companies); the [MCP Adapter](https://wordpress.org/plugins/mcp-adapter/) for any site (open project); [wordpress.org/hosting](https://wordpress.org/hosting/).
  How: Define a short, machine-readable entry (what the connector does, how to sign up); let any host list itself on equal terms; link the directory from the agent guide.
  Where: [make.wordpress.org/hosting](https://make.wordpress.org/hosting/)
  How we'll know: Agents name a way to put a WordPress site live, and "Hosting and upkeep" falls below 82% by more than the margin.

<!-- answers: scale=new reasons=upkeep claims=paid-hosting-cost,agent-cannot-run-it,hosted-managed-options conditions=hosted-low-maintenance -->

## Where WordPress isn't the best fit

- **A one-page site nobody edits.** Static files are cheaper and simpler. Agents said so fairly: "that would be overkill for one page and adds upkeep" (C2610-0006).
- **A single video course.** Hosted course platforms bundle video, checkout and student logins. For course sites, agents named Teachable (16 mentions) and Podia (13) most, and WordPress wasn't in their top eight. On WordPress, video needs a separate video host or a plan that includes one.
- **An owner who wants no setup and no upkeep at all.** A hosted builder can be simpler. That was a reason at 8% of sites (16 of 193).

## About the numbers

- **Sample.** 193 sites from one batch, built by seven agent and model pairs. Per-agent numbers are in the data, not here.
- **How shares are counted.** Each share is a share of all 193 sites, and a site counts once per claim.
- **Margin of error.** About ±7 points near 50% and ±4 points near 10%. No month-on-month change is claimed.
- **What the conditions are.** Conditions for when WordPress fits are mostly what agents said after building. That is weaker evidence than what they did.
- **Fact checks.** Facts were checked against dated sources on 7 Oct 2026. Benchmark figures themselves can't be confirmed outside the benchmark.

## What this doesn't cover

- **Personal agents with their own hosting.** OpenAI's dots, Meta's Muse and xAI's Grok Bot haven't been tested. Whether they can put a WordPress site live may decide the choice for them.
- **Consumer chat apps.** These discover platforms through connector directories, which this batch didn't test.
- **Succeeding once WordPress is chosen.** That is the Building benchmark's job.
