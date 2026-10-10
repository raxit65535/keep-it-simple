# Keep It Simple

Raxit Solanki's engineering and research portfolio, built with **Quarto** and
published to [GitHub Pages](https://raxit65535.github.io/keep-it-simple/).

The public site connects projects, research, technical writing, publications,
and presentations. The existing **LangGraph research framework** remains an
optional, autonomous authoring tool—not part of the website build.

**Start here:** this README covers setup and authoring. Read
[HANDOFF.md](HANDOFF.md) for completed work, engineering decisions, known limits,
and continuation steps; [AGENTS.md](AGENTS.md) contains the agent working rules.
These files are the portable project memory. Local agent transcripts and scratch
are deliberately not part of a clone.

## Setup

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and the
standalone [Quarto CLI](https://quarto.org/docs/download/). Use the version in
[`.quarto-version`](.quarto-version), currently **1.10.19**. Python **3.13** is
selected by [`.python-version`](.python-version); uv manages the environment.

```sh
quarto --version
uv sync --frozen
```

Quarto is a separate executable, not a Python renderer package. If using the
portable copy installed locally during migration, enable it in the current shell
from the repository root:

```sh
export PATH="$PWD/.local/quarto/1.10.19/bin:$PATH"
quarto --version
```

That portable directory is ignored and is not included in fresh clones. Install
Quarto from its official release distribution on other machines. CI installs
the same pinned version automatically. No task runner or manual venv activation
is required.

### Continue on another laptop

First **manually review, commit, and push** the source branch you want to continue.
A GitHub clone cannot contain uncommitted changes or commits that were never
pushed. During this preparation the branch is `raxit65535/eng-framework`; use
`main` instead only after the work is actually merged there.

After installing Git, uv, and the pinned
[Quarto release](https://github.com/quarto-dev/quarto-cli/releases/tag/v1.10.19),
use these commands in a terminal (macOS/Linux shell shown):

```sh
git clone --branch raxit65535/eng-framework https://github.com/raxit65535/keep-it-simple.git
cd keep-it-simple
uv python install 3.13
quarto --version                         # must match .quarto-version
uv sync --frozen                         # core + dev; no LLM stack
uv run --frozen python -m tools.build_site
uv run --frozen pytest -q
uv run --frozen ruff check .
quarto preview docs --port 8000 --no-browser
```

Replace the branch in the clone command if you pushed a different one. Do not
copy `.venv/`, `.local/`, generated HTML, or browser sessions between machines:
install tools and regenerate outputs. The regular build/tests need no LLM API
key, running model, private notes, or agent-session files. Quarto must be on PATH
so renderer tests run instead of skipping. Browser smoke checks are optional.

Install the optional agent stack only when needed:

```sh
uv sync --frozen --group agent
uv run --frozen --group agent python -m research_agent --help
uv run --frozen --group agent pytest -q
```

Configure your model service and any credentials separately on the new machine;
never transfer them through Git. `uv run` does not automatically load `.env`.
If you deliberately use an ignored environment file, pass `--env-file .env` to
`uv run`, or supply environment variables through your shell/password manager.
Real agent searches can access the network even with `--no-llm`.

## Everyday commands

```sh
quarto preview docs --port 8000 --no-browser   # http://127.0.0.1:8000
uv run python -m tools.build_site             # clean, strict public build
uv run python -m tools.new_post               # interactive draft scaffolding
uv run pytest -q
uv run ruff check .
uv run ruff format .
```

`tools.build_site` checks the Quarto version, validates source paths/metadata,
cleans only `docs/_site/`, renders without executing computations, generates
compatibility redirects, and checks internal links, citations, search, sitemap,
and publication boundaries. It never deploys. A successful preview alone is
not a release check.

For a renderer outside PATH, pass its executable explicitly:

```sh
uv run python -m tools.build_site --quarto .local/quarto/1.10.19/bin/quarto
```

## Layout

| Location | Purpose |
| --- | --- |
| `docs/_quarto.yml` | Authoritative public site configuration |
| `docs/contributions/` | Project descriptions, evidence, and artifacts |
| `docs/research/`, `docs/reading/`, `docs/publications/` | Research navigation and distinct content collections |
| `docs/posts/<slug>/index.qmd` | Approved public articles |
| `docs/writing/` | Native article listing; its empty YAML catalog supports zero posts without warnings |
| `docs/talks/`, `docs/about/` | Presentations and professional profile |
| `docs/service/` | Reviewing and professional-service records |
| `docs/recognition/`, `docs/awards/`, `docs/memberships/`, `docs/media/` | Clearly labeled professional-record collections |
| `docs/_quarto.yml` → `website.sidebar.header`, `docs/assets/profile.jpg` | Native Quarto profile bio and photograph |
| `docs/_site/` | Generated public output, ignored by Git |
| `drafts/` | Generated local drafts, ignored; not deployed |
| `templates/` | Unpublished post, paper-analysis, project, publication, and talk templates |
| `config/authors.yml` | Author IDs for scaffolding and agents |
| `config/redirects.yml` | Retired URLs mapped to the Writing collection |
| `research_agent/` | Retained autonomous LangGraph workflow |
| `HANDOFF.md`, `AGENTS.md`, `README.md` | Public-safe, committable project memory and contributor guidance |
| `.agent/` | Ignored local plans, research runs, audits, and scratch; not portable project memory |
| `.superpowers/`, `.local/` | Ignored session artifacts and machine-local tools |
| `.personal/` | Ignored local personal notes; never a public or CI input |

The site uses a dark-first academic layout, taking organizational cues from
[Andrew Heiss](https://www.andrewheiss.com/) and [Emi Tanaka](https://emitanaka.org/),
with a native light/dark toggle that remembers an explicit reader choice. The first entry in `format.html.theme`
sets the default; keep `dark` first. The profile sidebar is native Quarto, styled
with ordinary CSS rather than a custom frontend framework. Keep its bio as an
inline fenced Markdown block in `website.sidebar.header`: Quarto 1.10.19 resolves
file-based headers relative to each page, which breaks them on nested routes.
Use project-root-relative paths for any internal links in the shared bio.

Professional record sections remain visible as you build the portfolio.
[Publications](docs/publications/index.qmd) contains source-linked thesis,
conference-paper, and journal-article records with local BibTeX. Unpopulated
collections retain honest empty states. Use
[professional record snippets](templates/professional-records.md) to add a real
entry, replace its `.collection-empty` block, and set the collection's
`record-status` to `populated`. This is an editorial status, not an assessment of
an achievement. Existing forked repositories retain upstream attribution.

Publication details follow publisher, DOI-registration, or archive records rather
than copying profile metadata uncritically. Preserve author order and source-date
precision. [Recognition](docs/recognition/index.qmd) separates institution-level
context, such as CSUF's citation-impact ranking, from personal awards.

The two starter posts have been removed. No example research results or
publication records were invented to populate empty collections.

## Authoring and publishing an article

`uv run python -m tools.new_post` creates `drafts/<slug>/index.qmd` with `img/`
and `assets/` directories. It emits native YAML, an explicit title, and
`draft: true`. Author IDs must exist in `config/authors.yml`.

- Use the description as listing/SEO text; no special excerpt marker is needed.
- Keep images and bibliography files beside the article and reference them relatively.
- Add `bibliography: references.bib` to front matter and cite with `[@citekey]`.
- Use ordinary code fences for display, native math, callouts, and Mermaid fences.
- Use the templates for other content types. They remain outside the public build.
- Distinguish content kind, editorial draft state, research stage, publication
  status, and evidence status. A preprint is not a peer-reviewed publication.

Preview a draft directly with `quarto preview drafts/<slug>/index.qmd` (replace
`<slug>` with the actual directory). After reviewing it, copy **only that bundle**
to `docs/posts/<slug>/`, set `draft: false`, and run the strict build. Do not merge
into an existing destination accidentally; overwrite is always an explicit action.
The public project rejects drafts rather than risking publication of their assets.

The Writing listing automatically includes new public articles. To enable its
native RSS feed after adding content, set `listing.feed: true` on
`docs/writing/index.qmd`, build, verify the generated feed, and then add its link.
An empty collection does not advertise a nonexistent feed.

### Other content types

Only **Writing** auto-lists articles today. Other collection indexes are curated
Markdown: add a link when publishing a child page. A new directory alone does not
make its record discoverable.

| Content | Starting point | Public destination / index |
| --- | --- | --- |
| Post or technical guide | Post CLI or [post template](templates/post.qmd) | `docs/posts/<slug>/index.qmd`; automatic Writing listing |
| Analysis of another paper | [Paper-analysis template](templates/paper-analysis.qmd) | `docs/reading/<slug>/index.qmd`; link from Reading |
| Engineering project | [Project template](templates/project.qmd) | `docs/contributions/<slug>/index.qmd`; link from Projects |
| Original study, protocol, or results | Adapt the project template to the research stage | `docs/research/<slug>/index.qmd`; link from Research |
| Your publication | [Publication template](templates/publication.qmd) | `docs/publications/<slug>/index.qmd`; link from Publications |
| Talk or demonstration | [Talk template](templates/talk.qmd) | `docs/talks/<slug>/index.qmd`; link from Talks |
| Service, awards, memberships, or coverage | [Record snippets](templates/professional-records.md) | Update the matching collection or link a child page |

The CLI scaffolds posts only; there is no `--kind`, new-project, or promotion
command. For other records, start from a template under `drafts/`, replace the
prompts, and review the complete bundle before copying it into `docs/`. Set
`draft: false` only for approved public content. Keep standalone draft previews
non-executing with `execute.enabled: false` in their metadata.

Use one canonical record per project/publication and link related code, data,
articles, and talks to it. Distinguish ideas, implemented work, measured results,
and independent corroboration. Bibliographic records should preserve full author
order, venue, source-date precision, and DOI/archive links. Prefer publisher or
archive metadata when a profile differs. A local `references.bib` supplies native
citations; link permitted external PDFs rather than copying restricted material.
A metadata check does not independently validate scientific findings.

The current autonomous agent drafts literature reviews; it does **not** implement
or run original experiments. Keep experiments, manuscripts, and slide exports in
their appropriate separate environments, then publish reviewed artifacts here.

### Computation and supported public sources

Run experiments/notebooks in their own environments and publish reviewed
results, static figures, or links to versioned artifacts. Website builds disable
computation explicitly; do not rely on freeze settings as a security boundary.
Optional manuscript PDF exports and RevealJS slides are separate authoring
workflows and do not impose LaTeX or experiment dependencies on site CI.

The strict builder supports ordinary Quarto Markdown, local assets, citations,
and video shortcodes. It deliberately rejects external file references, source
symlinks, custom engines/filters/hooks, filesystem/environment shortcodes, and
file-based custom themes. Use stock themes and CSS. Quarto may expand active
shortcodes even in code examples; use Quarto's escaped syntax for examples.
Public builds explicitly target HTML and reject other format declarations;
export manuscripts and slide decks separately. An empty render without a
homepage is a failed build, even if Quarto exits successfully. This is an
accidental-publication guard for a supported authoring surface, not a sandbox
for arbitrary hostile extensions.

Sidebar, body, and margin header/footer file references are checked before
rendering. For shared content, prefer inline fenced Markdown blocks and use
project-root-relative internal links; their Markdown/HTML links are checked too.
Sensitive filenames such as `.env*`, key containers, and credential exports are
rejected anywhere under `docs/` and in public output—even if unreferenced or
explicitly selected as resources. Keep safe `.env.example`/`.env.template` files
outside `docs/`; public examples belong in ordinary Markdown code fences.
These filename/path guards are **not a secret-content scanner**: review real
content and run a redacted secret scan before publishing substantial changes.

## Autonomous research workflows

```sh
uv sync --frozen --group agent
uv run --group agent python -m research_agent --help
uv run --group agent python -m research_agent "your research question"
uv run --group agent python -m research_agent "your question" --no-llm
```

The retained stages are **search → screen → synthesize → store → publish**.
There are no new approval prompts between research stages.

- `KIS_LLM_PROVIDER`: `ollama` (default) or `openai`.
- `KIS_LLM_MODEL`: model override; use the provider's normal local service/API setup.
- `--no-llm`: deterministic writing; **retrieval still uses the network**.
- Default dry run: writes a four-file Quarto bundle under
  `drafts/<run-id>/<slug>/`, with bibliography and source/social sidecars; no Git
  or remote actions. Scratch candidates/kept records remain in `.agent/runs/`.
- `--no-dry-run`: starts a run, prepares the site article on `research/<slug>`,
  and opens a review PR. It never merges or deploys. The PR contains the intended
  public page, so no second promotion is needed after an approved merge.
- PR creation requires a clean tracked/index state, no unrelated untracked work,
  an unused destination/branch, and an installed/authenticated `gh` CLI. The
  exact bundle is committed; failures preserve files and report the reached stage.

The current writer uses truncated abstracts. Venue/citation/recency ranking is
only a discovery heuristic. Bundles carry an **unverified literature draft**
disclosure, and AI-assistance metadata reflects whether the run used an LLM.
Verify full sources and claims before publication. Do not put API keys or private
material into articles, logs, or repository history.

Optional-stack tests use synthetic retrieval and make no live model calls:

```sh
uv run --group agent pytest tests/test_graph_workflow.py -q
```

A normal install skips that integration module. Real-render tests run when the
pinned Quarto executable is on PATH; the release verification should run them.
For an optional real-Chrome mobile/dark-mode smoke check after building, run
`uv run tests/browser_smoke.py`. Its inline uv dependency declaration supplies
WebSocket support; it uses an isolated temporary browser profile and local server.

## GitHub Pages deployment

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) validates PRs and pushes,
then publishes only authorized `main`/`release` push or manual-dispatch runs.
Validation has read-only permissions; the dependent publishing job has repository
write permission and publishes the **already validated** `docs/_site/` artifact.
No model calls or personal-notebook builds run in CI. Per-ref workflow
concurrency cancels superseded runs; deployment remains serialized across refs.
Both source branches target the same website, so their latest successful
approved deployment determines its content.

Existing Pages settings remain **Deploy from branch → `gh-pages` → `/`**, with
no custom domain. There is no required initial local publish. Do not publish
manually or change Pages settings as a setup shortcut.

Compatibility redirects retain the old inspiration, Ubuntu, tags, archive, and
category URLs, leading to Writing. These are static HTML redirects, not HTTP 301
responses. All URLs use the `/keep-it-simple/` project prefix.

After the first approved deployment, check Home, About, Writing, one old URL,
images, search, and the sitemap on the hosted site. Local build success does not
mean that the live deployment has already changed.

## Local data and privacy

`.personal/`, `drafts/`, `.agent/`, `.superpowers/`, local tools/environments,
IDE state, environment-file variants, and common credential/key files are ignored.
Only placeholder-only `.env.example` and `.env.template` files are exceptions to
the environment-file ignore rule; neither may contain real credentials.

Ignored material does **not** travel with a Git clone. Use a separate secure,
appropriately encrypted transfer/backup for any private notes or unfinished drafts
you actually want on the new laptop. Do not unignore them to move machines, and do
not copy private content into the shared handoff. API credentials should come
from a password manager or be reissued; local model downloads can be reinstalled.
Ignoring files is not encryption and does not remove previously committed data.
The public site must build without any of these local directories.

A local notebook may have its own Quarto configuration under `.personal/`.
Use an explicit `project.render` file list there: the pinned renderer's default
directory discovery can skip a hidden ancestor and exit without creating HTML.
Keep its content and output out of public pages, CI artifacts, and shared plans.

### Before your eventual commit and push

Nothing is staged or committed automatically by the readiness workflow. Review
both the existing index and working tree; this checkout may already contain
staged changes that differ from the files on disk:

```sh
git status --short
git diff --stat
git diff --cached --stat
git ls-files -- .personal/ .agent/ .superpowers/ .local/ .idea/
```

The last command should print nothing. Review and include the intended source,
assets, templates, tests, tooling, configuration, version pins, `uv.lock`, and
`README.md`/`AGENTS.md`/`HANDOFF.md`, as well as the intentional legacy-file
deletions. Do not use force-add to bypass private-data ignores. Make sure your
reviewed `.gitignore` changes are included; working-tree ignores alone do not
update an already-staged version.

Run the strict build, tests, lint, and a redacted secret scan on the final commit
candidate. Public contact details and CV/business metrics still need your
explicit disclosure judgment. Only after your own review should you commit and
push the chosen source branch. Pushing `main` or `release` triggers deployment;
pushing the feature branch does not. On the new laptop, ask the agent to read
`AGENTS.md` and `HANDOFF.md`, inspect the current Git state, and run the setup checks
before continuing. Update those documents as decisions or verified behavior change.
