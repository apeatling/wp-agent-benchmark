# Principles for the benchmark's recommendations

The analysis that drafts recommendations and strategy loads this file every time and grounds everything in it. Edit it
like code: changes are reviewed and versioned.

## It's public record

WordPress is an open source project. Everything the benchmark publishes, strategy included, is public. There is no
internal version. Write so a team named in it would recognise itself fairly, nothing would surprise or embarrass them,
and readers nod and want to act.

- Describe agent behaviour, not blame. Don't single out one agent, lab, team or company as the problem. Per-agent
  numbers live in the data, not in the argument.
- Credit existing work before asking for more. Name the projects already doing it, and build on them rather than
  proposing something new.
- Invite rather than instruct. Say who is well placed to help, not who must do what.
- Frame open decisions as questions for the project and its community, not as instructions to leadership.
- Concede where WordPress isn't the best fit, such as a one-page site nobody edits. Credibility on the rest depends on it.
- Lead with opportunity, not loss, without hiding the result.

## Core, and the ecosystem around it

People using agents to build with WordPress have to be able to succeed, the same way they can in a web browser. That
foundation is core: starting a site, building it correctly, converting an existing site, operating it through abilities,
a portable site format, and neutral guidance on when WordPress fits.

Hosting, and customised or enhanced experiences on top, are the job of the community and commercial companies: hosts,
WordPress.com, plugin and theme businesses, agencies. The open project provides shared foundations so these companies
can offer above-and-beyond service and compete on it. Don't push core so far that it takes that over, and don't
undercut paid offerings when correcting facts: say what free options exist and what paid ones add.

For every opportunity, separate what the open project can provide from where the ecosystem can build.

## The open project is not any one company

WordPress.org (core, its teams, wordpress.org, the WordPress GitHub organisation) is the open project. Automattic,
WordPress.com and its products (Studio, Telex, the WordPress.com MCP server and others) are a company in the ecosystem,
alongside other hosts, plugin and theme businesses and agencies. Contributors employed by a company still work on the
open project; what matters is who stewards the thing.

- Be host and company agnostic. Give no company more weight than another, however much it has published.
- What the open project should provide is never a company's product. A company tool can be cited as one example of
  what the ecosystem offers, next to others where they exist, and labelled as a company product.
- If only one company offers something agents need to succeed with WordPress, treat that as a gap the open project or
  the wider ecosystem should close, not as the answer.
- Recommendations that depend on one company's service aren't host agnostic. Say so if there's no alternative yet.

## Choosing is about being chosen

The Choosing benchmark's advice is only about helping WordPress be chosen more often: the moment an agent decides how
to build, what it knows, what it asks, what it believes. Succeeding once WordPress is chosen (starting, building,
converting, operating, going live) is the Building benchmark's job, with its own recommendations. But whether something
is possible at all changes the choice: when agents avoid WordPress because they believe it can't start where they are,
can't take their existing HTML, or can't go live, the tool that makes it possible is a Choosing idea.

## Before the choice

Every idea has to reach an agent that hasn't chosen WordPress yet. Ask of each one: how does an agent that has never
been told about WordPress meet this, before it decides? Only a few routes exist:

- What models learn: docs, examples, templates, tutorials and facts published widely enough to shape training data.
- What agents find while they work: web search, docs they fetch, package registries (`npx`, `npm`), error messages.
- What ships inside the agent: connector and tool directories its maker includes by default.
- What labs measure: public evals and benchmarks that models are trained and judged against.

Anything installed into the agent or the site first (a WordPress skill, plugin, MCP server or theme) only reaches an
agent after someone has already chosen WordPress. However useful, it doesn't change the choice, so it isn't a Choosing
idea: list it for the Building benchmark instead. Agent makers bundling something by default isn't the project's
decision. Tooling that removes a reason not to choose WordPress (a one-command start, a converter, a deploy path) is
different: it counts, paired with the practical content that tells agents it exists. Pointing agents to company tools
isn't the answer when only companies offer something; the open project closing the gap is.

## Content and tooling

Separate three kinds of idea, because they reach agents differently and change different things:

- Persuasion: content arguing that WordPress fits ("WordPress is great for a newsroom"). Agents mostly know this
  already and say so after building, so persuasion rarely changes what they do. Rank it low unless the evidence shows
  agents didn't know.
- Practical content: what an agent needs to act, stated plainly where it learns or looks. One command to start, real
  prices, a working example, a dated fact. It corrects what agents believe they can't do or can't afford.
- Tooling and product changes: commands, importers, connectors, deploy paths, defaults in core. They change what's
  true and what an agent can deliver. An agent told to build picks what it can run and show straight away, so what it
  can deliver often decides the choice. Tooling only moves the choice if agents can learn it exists before choosing:
  pair it with the practical content that announces it.

Weigh evidence the same way: what got in the way while the agent was deciding, and at sites where it nearly chose
WordPress, shows what changes choices. Reasons given when asked afterwards are weaker; they're often an explanation
of a choice already made.

## Only what the project and its ecosystem can do

Every idea is something WordPress contributors, teams or ecosystem companies can actually do: ship, publish, change
or start. Agent makers' behaviour isn't ours to change, so don't recommend it ("agents should ask who will update the
site"). Recommend what the project can do to influence it instead. Each idea's title is that action, starting with a
verb.

## Rank by impact, honestly

Give every idea an impact rating, High, Medium or Low, with one plain sentence saying why. Impact is how much the idea
would raise the share of sites agents build with WordPress: how often the problem it answers got in the way, times how
surely and how soon it reaches agents before they choose. Be strict. High is rare and needs a clear route to agents
and a problem that came up often. A large effort with an uncertain route to agents is Low, however good the idea.
Ratings are judgements; say what each rests on.

Look widely for ideas. The evidence holds more than the obvious fixes: read the near misses, what would have changed
agents' minds, and the alternatives they chose, and ask what the project could do about each. Bold ideas are welcome,
rated as honestly as the rest.

## Brief, and pointing to references

Say what matters and stop. Fewer, sharper points beat full coverage. Leave a field out rather than pad it, and link to
the source, project or discussion instead of restating it. Nobody reads a long report; the page shows the headline and
lets people open the detail.

## Evidence

- Every number comes with its sample size, and claims of change only beyond the margin of error.
- Every number explains itself: what was counted, out of what, in plain words, and why it matters to the point it
  supports. A percentage on its own means nothing to a reader.
- Quotes are verbatim, from a named run.
- Facts come with a dated source. Unconfirmed figures aren't used in anything agents or the public will read.
- Say where the evidence is thin.

## Independence

The analysis is written from the evidence, the facts and the landscape of what's in flight. People's own strategic
ideas are tested separately, afterwards, so they don't steer it.
