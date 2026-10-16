# Personal agents: what their computers are like

Building tests coding agents today. Personal agents with their own computer (Grok Bot, Muse, OpenAI dots) are a later group. Their makers don't publish an image or a way to run them in a controlled setup, so they'll be run as **labelled approximations**: the product's own model, on a computer set up as close to the product's as public information allows. This file keeps what's known, and where it comes from. Researched 14 October 2026; check again before building.

Confidence: **official** (the maker's own docs or posts), **community** (users inspecting their own machine and posting it), **unconfirmed** (one source, or sources disagree).

## Muse (Meta)

Launched 8 September 2026. Better documented than the others: Meta published how it's built.

| | | Confidence |
|---|---|---|
| Model | Muse Spark 1.3 | Official |
| Machine | An isolated Linux VM per user ("Muse Secure VM") | Official |
| Agent's environment | A container (systemd-nspawn) with a full Debian image as its root; unprivileged, filtered system calls (no io_uring), limited capabilities (no CAP_NET_ADMIN) | Official |
| Host OS | Ubuntu 24.04, kernel 7.0 | Community |
| Resources | 2 vCPU (AMD EPYC), about 8 GB RAM (7.7 GB measured), 100 GB disk, no swap, no GPU | Community |
| Browser | Up-to-date Chromium-based, outside the agent's container, reached through a broker (Chrome DevTools Protocol). The agent sees an accessibility tree, not the page's code; it can't run JavaScript in the page; DevTools are off | Official |
| Terminal | Yes: file system and terminal; can install software and compile code | Official |
| Network | Every request goes through a forward proxy to Sentinel, which allows, denies or **asks the user** (in the app, not the chat). Checks host, IP, port, method, path. Processes that have read user data lose automatic approval | Official |
| Logins | Stored by a credential service (hatch-authd) in the user's VM; the agent only sees stand-in tokens, swapped for the real ones at the network edge. Browser passwords are filled in at the point of use | Official |
| Home folder | /home/hatch, with memory as Markdown files | Community |

**Asked Meta (15 October 2026):** on X, Tarek Sheasha (Muse) pointed to the safety post below as the spec. We replied asking for a way to run Muse programmatically in its normal environment, or a test account. Waiting on an answer.

For an approximation: the browser can't be scripted, and Sentinel's "ask the user" step means the scripted owner must answer approval requests (reaching a new site, signing in), as a real owner would.

Sources:
- [Meta: How We Built Safety Into Muse](https://research.meta.ai/blog/security-and-safety-for-ai-agents-our-approach-with-muse) (official, the main source)
- [Meta: Introducing Muse](https://about.fb.com/news/2026/09/introducing-muse-personal-ai-agent/) (official)
- [How We Designed Muse](https://introducing.muse.ai) (official)
- [Mark Zuckerberg on X](https://x.com/finkd/status/2097402102477701478)
- [Tanay Jaipuria on X: VM specs](https://x.com/tanayj/status/2101835047489982524)
- [The Decoder: Muse runs Ubuntu Linux](https://the-decoder.com/metas-muse-agent-gives-every-user-a-full-cloud-computer-running-ubuntu-linux/)
- [Tom's Hardware: Muse hosts](https://www.tomshardware.com/pc-components/cpus/meta-muse-runs-agents-on-amd-epyc-turin-hosts-with-two-cores-and-8gb-of-memory-ai-agent-can-pass-terminal-commands-to-ubuntu-host-system)
- [Vellum: Official Muse Breakdown](https://www.vellum.ai/blog/official-muse-breakdown)

## Grok Bot (xAI)

Launched in beta 11 August 2026, distributed with Cursor. Little is documented beyond what the computer is for.

| | | Confidence |
|---|---|---|
| Model | Grok; the exact version isn't stated (Grok 4.6 shipped the day after launch). Check inside the app | Unconfirmed |
| Machine | One persistent cloud computer per account, shared by all your Bots (files, browser sessions, logins); each Bot gets its own screen | Official |
| OS | Debian Linux (one review says Ubuntu) | Community |
| Desktop | Chrome, a terminal, Thunar file manager (suggests Xfce) | Community |
| Resources | About 8 vCPU, 16 GB RAM, 128 GB disk (one `df` showed 126 GB) | Community |
| Files | /workspace | Official |
| Admin access | Reportedly available | Unconfirmed |
| Maintenance | Update (keeps files), Reset (rebuilds from the last snapshot), Recover | Official |
| API | None for driving Bots; one developer found a webhook-triggered routine as the only programmatic start | Community |

Reportedly powered by Cursor's cloud-agent technology; Cursor documents its own cloud environment (Ubuntu base, customised with a Dockerfile), the nearest documented relative.

**Self-reported image (14 October 2026):** asked for its base computer, Grok Bot wrote a Dockerfile, saved as [personal-agents/grok-bot/Dockerfile](personal-agents/grok-bot/Dockerfile): Debian 13.7 (trixie) x86_64, apt frozen to the 5 October 2026 Debian snapshot, Chrome 154.0.8037.97, Python 3.13, Node 20, Rust 1.85, pinned Python libraries, user `box`, /workspace, a 1280×800 Xvfb screen with VNC. Confidence: unconfirmed until the versions are checked against the Bot's own output (a model can write plausible version numbers). It leaves out the desktop (Xfce/Thunar), the CPU and memory limits, and the agent itself.

To pin it down: in a Bot, ask it to run `cat /etc/os-release`, `uname -a`, `nproc`, `free -h`, `df -h /`, the Chrome version, and list installed packages and tools.

Sources:
- [xAI docs: Grok Bot computer and apps](https://docs.x.ai/grok-bot/computer-and-apps) (official)
- [xAI docs: Grok Bot FAQ](https://docs.x.ai/grok-bot/faq) (official)
- [xAI docs: Grok Bot overview](https://docs.x.ai/grok-bot/overview) (official)
- [xAI news](https://x.ai/news)
- [Robin on X: Debian, Chrome, Thunar, 16 GB, 128 GB](https://x.com/xdNiBoR/status/2087241709574820188)
- [QCode: community VM specs](https://qcode.cc/en/grok-bot-16g-128g)
- [Sortwell: GrokBot review](https://sortwell.net/en/ai-tools/grok-bot-review)
- [DEV: How I Have Claude Code Control Grok Bot (There Is No API)](https://dev.to/danmercede/how-i-have-claude-code-control-grok-bot-there-is-no-api-14oh)
- [Cursor docs: Cloud environment setup](https://cursor.com/docs/cloud-agent/setup)
- [Cursor blog: How we set up our cloud agent environment](https://cursor.com/blog/cloud-agent-environment)

## OpenAI dots

Launched 29 September 2026 at DevDay, in ChatGPT (Pro and Business Premium first; not in the EEA, Switzerland or the UK on Pro at launch). OpenAI documents the behaviour well (announcement, system card appendix, Help Center) but not the machine.

| | | Confidence |
|---|---|---|
| Model | GPT-6 Astra (not GPT-6.1-Sol, the model our Codex runs use). The system card compares Astra in the Codex and dots harnesses | Official |
| Machine | Its own cloud computer and its own browser per dot; you can open the computer to inspect its work; your own computer stays separate unless you connect it (off by default, desktop app only) | Official |
| OS | Debian 13.6, kernel 6.18.44, x86_64 (one Geekbench listing shows Ubuntu 24.04.3; the Debian reports are more detailed) | Community |
| Resources | AMD EPYC 9V74, 9 vCPU, 9.73 GiB RAM, no swap, about 31.5 GiB workspace disk (29.7 free), no GPU | Community |
| Browser | Chrome (or Chromium), maintained by OpenAI | Official that there's a browser; build is community |
| Terminal | Yes, with a file manager; no sudo, no writing to /usr/bin or /opt; reportedly no Docker | Community |
| Network | Restricted: one user found the terminal had no general internet access (couldn't download a package); the browser and connected apps are the way out | Community |
| Apps | Connected through ChatGPT's plugins (over 4,000 apps), managed in ChatGPT's app controls | Official |
| Logins | Saved passwords can be used to sign in to supported sites without exposing them to the model | Official |
| Approvals | Built-in rules for acting alone vs asking; Custom Rules can allow, require approval for, or block actions; auto-review checks actions that could affect accounts or share information; some tasks (like changing a password) always stay with the user | Official |
| Background work | "Proactive research" uses connected apps with read-only tools: it can't send messages, change app content or drive the browser or computer | Official |
| Work style | Delegates to subagents; a time-budget setting guides how long it works | Official |
| Persistence | Unclear whether the same machine stays allocated between sessions | Unconfirmed |
| API | None for driving dots found | Community |

For an approximation: GPT-6 Astra on Debian 13 with Chrome, a terminal without sudo and with limited network, about 9 vCPU and 10 GB. The approval rules matter most: changing a WordPress site counts as changing app content, so a dot will often stop to ask, and the scripted owner must answer as a real owner would.

Sources:
- [OpenAI: Introducing dots](https://openai.com/index/introducing-dots/) (official)
- [OpenAI: GPT-6 Astra System Card, Appendix: dots](https://deploymentsafety.openai.com/gpt-6-astra) (official)
- [OpenAI Help Center: Getting started with your dot](https://help.openai.com/en/articles/20001530-getting-started-with-your-dot) (official)
- [OpenAI: GPT-6 Astra](https://openai.com/index/gpt-6-astra/) (official)
- [Unexcited Neurons: dots come with a surprisingly capable Linux environment](https://unexcitedneurons.substack.com/p/openais-dots-come-with-a-surprisingly)
- [Tom's Hardware: Geekbench 7 suggests nine-core AMD EPYC VMs](https://www.tomshardware.com/tech-industry/artificial-intelligence/geekbench-7-results-suggest-openais-dots-agent-runs-on-nine-core-amd-epyc-vms-with-nearly-10gb-of-memory-newest-runs-score-about-six-times-meta-muse-in-multi-core)
- [Wccftech: dots VM on AMD EPYC 9V74](https://wccftech.com/openais-dot-vm-is-hosted-on-an-amd-epyc-9v74-80-core-processor-where-each-9-core-vm-instance-has-9-73-gb-of-memory-and-sports-a-multi-core-score-of-9435-on-geekbench-7/)
- [SmartScope: dots VM specs and Grok Bot comparison](https://smartscope.blog/en/blog/openai-dots-vm-specs-sudo-access-grok-bot-2026/)
- [OpenAI Developer Community: Docker support for dots](https://community.openai.com/t/docker-container-support-for-dots-working-in-the-cloud-computers/1402440)
- [DEV: dots permission model, from the docs](https://dev.to/sword_luan_6dfb4e81cf5f15/openai-dots-explained-from-the-docs-the-permission-model-of-an-always-on-agent-5eoj)
- [CNBC: DevDay recap](https://www.cnbc.com/2026/09/29/openai-devday-2026-live-updates.html)
