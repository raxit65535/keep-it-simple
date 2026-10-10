# Using and extending Keep It Simple

A practical handbook for growing this repository from a portfolio into a
connected collection of technical writing, research, and reproducible work.

**Start here:** write outside the public site, publish one reviewed content
bundle, link it from the appropriate collection, and run the strict build.
You do not need a new plugin or framework for each article.

This guide describes the current implementation. Examples of future projects
and filenames are illustrative, not claims about completed work. For installation
and deployment basics, see [README.md](README.md).

## Contents

1. [Understand the three workspaces](#1-understand-the-three-workspaces)
2. [Choose where each type of content belongs](#2-choose-where-each-type-of-content-belongs)
3. [Write and publish your first post](#3-write-and-publish-your-first-post)
4. [Write technical guides](#4-write-technical-guides)
5. [Review a research paper](#5-review-a-research-paper)
6. [Document projects and implement research ideas](#6-document-projects-and-implement-research-ideas)
7. [Add your publications and references](#7-add-your-publications-and-references)
8. [Connect talks, slides, and videos](#8-connect-talks-slides-and-videos)
9. [Use the autonomous research framework](#9-use-the-autonomous-research-framework)
10. [Extend the site and the agents](#10-extend-the-site-and-the-agents)
11. [Maintain the collection](#11-maintain-the-collection)
12. [Troubleshooting and a publishing checklist](#12-troubleshooting-and-a-publishing-checklist)

## 1. Understand the three workspaces

```text
Working area                 Publication source             Generated website
--------------------------   ----------------------------   ------------------
drafts/                      docs/                          docs/_site/
Write, revise, investigate -> Reviewed public content     -> HTML built by Quarto
Ignored by Git               Tracked with your changes      Ignored by Git
```

There are two additional local areas:

- `.agent/runs/`: ignored research-run inputs and intermediate records.
- `.personal/`: ignored personal knowledge. It is never an input to the public
  website, its search, or CI. Do not feed it to agents implicitly.

**A draft is a workspace state; public is a disclosure decision.** A working
research note may be intentionally public while its conclusions remain
exploratory. Conversely, a completed study may not be ready to disclose.

### The source of truth

Edit `.qmd` source files, not generated HTML. A `.qmd` file is Markdown with YAML
metadata and Quarto features. The site's configuration is
[`docs/_quarto.yml`](docs/_quarto.yml).

Treat everything placed in `docs/` as intended for public release, including
images, bibliography files, data extracts, and sidecars. Leaving a page out of
navigation does not make it private: Quarto renders the configured `.qmd` inputs,
and search or direct links can expose them.

Ignored files are not backed up by Git. Keep valuable drafts and research records
in an appropriate separate backup or research repository. Gitignore is not
access control and does not erase previously committed files.

## 2. Choose where each type of content belongs

Use one folder per article/project/record, usually with `index.qmd` and its assets.
Choose the destination by purpose, not by the tool that helped write it.

| You want to publish | Start from | Public destination | Discoverability today |
| --- | --- | --- | --- |
| Blog post or technical guide | Post CLI or [`post.qmd`](templates/post.qmd) | `docs/posts/<slug>/index.qmd` | Automatically included in Writing |
| Analysis of someone else's paper | [`paper-analysis.qmd`](templates/paper-analysis.qmd) | `docs/reading/<paper-id>/index.qmd` | Add a link to `docs/reading/index.qmd` |
| Engineering project / contribution | [`project.qmd`](templates/project.qmd) | `docs/contributions/<project-id>/index.qmd` | Add a link to the Contributions index |
| Research question, protocol, or results report | [`project.qmd`](templates/project.qmd), adapted to the stage | `docs/research/<project-id>/index.qmd` | Add a link to the Research index |
| Your paper or publication record | [`publication.qmd`](templates/publication.qmd) | `docs/publications/<publication-id>/index.qmd` | Add a link to the Publications index |
| Talk, video, or demonstration | [`talk.qmd`](templates/talk.qmd) | `docs/talks/<talk-id>/index.qmd` | Add a link to the Talks index |
| Biography, CV-style experience, contact links | Existing About page | `docs/about/index.qmd` | Already in top navigation |
| Reviewing and professional service | [Record snippets](templates/professional-records.md) | `docs/service/index.qmd` or a linked child page | Service navigation and home record links |
| Awards and honors | [Record snippets](templates/professional-records.md) | `docs/awards/index.qmd` or a linked child page | Recognition navigation and overview |
| Professional memberships | [Record snippets](templates/professional-records.md) | `docs/memberships/index.qmd` or a linked child page | Recognition navigation and overview |
| Media and external coverage | [Record snippets](templates/professional-records.md) | `docs/media/index.qmd` or a linked child page | Recognition navigation and overview |

**Only Writing is currently an automatic article listing.** The other collection
indexes are curated Markdown pages. Adding a folder renders its page, but does
not automatically add a card or link to those indexes.

The post CLI currently scaffolds posts only. For other types, copy a template;
there is no `new-project`, `new-publication`, or `--kind` CLI option today.

### Populate the professional-record placeholders progressively

The public record collections deliberately stay visible. Their empty states mean
that entries have not been added, not that an achievement is being claimed.

Use [professional-record snippets](templates/professional-records.md) for service,
awards, memberships, media, and contribution updates. For your first real entry:

1. Prepare and verify it in a draft; check source links, attribution, and disclosure permissions.
2. Replace the relevant `.collection-empty` block with the entry or a link to its page.
3. Change that collection's `record-status: awaiting-entries` to `record-status: populated`.
4. Keep its parent index and home links accurate, then run the strict build.

Do not publish bracketed template fields, sample dates, invented citations, or
empty evidence links. Keep compensation records and confidential supporting
material out of public pages. Forked repositories need upstream credit and an
explicit description of your own contribution.

Keep the recipient and scope of recognition explicit. University or employer
rankings may provide institutional context under `docs/recognition/`, but do not
populate `docs/awards/` as personal awards. Date the report, name the ranking's
actual metric, and link the original source.

### Metadata: what controls behavior and what records meaning

A typical article header:

```yaml
---
title: "Understanding Kafka offsets"
author:
  - name: Raxit Solanki
description: "A practical explanation of offsets, commits, and recovery."
date: 2026-10-08
categories: [Guides, Distributed Systems]
tags: [Kafka, Streaming]
kind: post
draft: true
ai-assisted: false
execute:
  enabled: false
---
```

Replace the example date with the article's actual date. Use `##` headings for
the body; Quarto renders the page title from the metadata.

| Field | How to use it |
| --- | --- |
| `title`, `description`, `author`, `date` | Native publishing metadata; title is required by the strict builder |
| `date-modified` | Add when updating an existing article; keep its original `date` |
| `categories` | Drives the current Writing category selector |
| `tags` | Retained metadata; the scaffolder also merges tags into categories for discovery |
| `bibliography` | Local BibTeX path for citations; omit it until the file exists |
| `draft` | Real YAML boolean: `true` while working, `false` for public content. Quoted `"false"` is not a boolean |
| `kind` | Content classification: `post`, `paper-analysis`, `project`, `publication`, or `talk` |
| `research-stage`, `publication-status`, `evidence-status` | Descriptive conventions used in templates; not automatic workflow gates or badges |
| `ai-assisted` | Record assistance honestly; changing it does not verify the content |
| `record-status` | Collection maintenance state: `awaiting-entries` or `populated`; not an assessment of the records |
| `project-origin` | Record a fork or another relevant origin; provide the actual upstream credit in the body |

If readers need to see a status, also write it in the page body. A metadata field
such as `evidence-status: unverified` is not automatically displayed as a warning.
The research agent adds an explicit disclosure to its generated article body.

`--author raxit` uses the ID in [`config/authors.yml`](config/authors.yml). The
scaffolder writes the display name into native Quarto metadata. Changing the
registry later does not rewrite previously authored pages.

## 3. Write and publish your first post

Run commands from the repository root. Install the pinned Quarto CLI and sync
Python tooling as described in the README. On this machine, the optional local
renderer can be added to the current shell:

```sh
export PATH="$PWD/.local/quarto/1.10.19/bin:$PATH"
uv sync --frozen
quarto --version
```

The `.local/` installation is not included in a clone; use the official installer
on other machines.

### Step 1: Create a draft

Interactive:

```sh
uv run python -m tools.new_post
```

Or provide the fields:

```sh
uv run python -m tools.new_post \
  --title "Understanding Kafka Offsets" \
  --author raxit \
  --description "A practical explanation of offsets, commits, and recovery." \
  --categories "Guides,Distributed Systems" \
  --tags "Kafka,Streaming"
```

This creates:

```text
drafts/understanding-kafka-offsets/
├── index.qmd
├── img/
└── assets/
```

The filename is always `index.qmd`; the folder slug is derived from the title.
Edit the generated file as the article develops. Do not rerun scaffolding to
revise a post: it refuses collisions unless you explicitly pass `--overwrite`.

### Step 2: Write, add assets, and preview

Use a relative image link, with meaningful alternative text:

```markdown
![Consumer commits and recovery points](img/offset-flow.svg)
```

Create that image before building. Do not include an example image path or
bibliography that does not exist.

For a standalone draft, keep `execute.enabled: false` in its front matter before
previewing. A draft outside `docs/` does not inherit the public site's settings.
Use ordinary code fences for displayed examples, not executable notebook cells.

```sh
quarto preview drafts/understanding-kafka-offsets/index.qmd --no-browser
```

Open the local URL printed by Quarto. A standalone preview checks the draft;
the final site preview is still needed for navigation, inherited styling, and
its position in the Writing listing.

### Step 3: Promote the reviewed source bundle

There is currently **no promotion command**. Copy the reviewed source deliberately.
The following creates a new public article directory and refuses an existing one:

```sh
mkdir -p docs/posts
mkdir docs/posts/understanding-kafka-offsets && \
  cp drafts/understanding-kafka-offsets/index.qmd \
     docs/posts/understanding-kafka-offsets/index.qmd
```

Then copy only the referenced `.bib` files and reviewed `img/` or `assets/`
content into that directory. Do **not** copy the whole output of a standalone
preview: it can contain generated HTML and support files. Inspect every file
that would become public, including data and provenance sidecars.

In the public `index.qmd`, change:

```yaml
draft: false
```

Keep the original draft if useful, but make subsequent published edits in
`docs/posts/understanding-kafka-offsets/index.qmd` to avoid maintaining two
competing copies. Back up any valuable ignored draft separately.

### Step 4: Check the complete site

```sh
uv run python -m tools.build_site
quarto preview docs --port 8000 --no-browser
```

Check Writing, the article, images, citations, and mobile layout. The public
source is already configured to disable computation; the strict builder also
forces HTML and `--no-execute`.

A rendered page has a URL such as:

```text
https://raxit65535.github.io/keep-it-simple/posts/understanding-kafka-offsets/
```

Keep the folder slug stable after publication. Editing the title does not require
moving the folder or breaking its URL.

### Step 5: Review your Git changes and publish through CI

```sh
git status --short
git diff -- docs/posts/understanding-kafka-offsets/
git diff --cached --stat
```

`git diff` does not display untracked files; inspect new files in your editor
as well. Stage only the article and any intentionally updated index/config files.
Review any existing staged work before committing—it would otherwise join a
normal commit. Do not use `git add .` as an authoring shortcut.

Use a normal source-branch PR. CI validates PRs; merging an approved change into
`main` or `release` triggers publication to the existing `gh-pages` branch.
Both branches target the same website, not separate staging/production sites.
No manual `quarto publish` or Pages settings change is needed.

## 4. Write technical guides

A guide uses the post workflow and `kind: post`, with a category such as `Guides`.
A useful structure is:

1. Audience, goal, and prerequisites.
2. Exact environment/version assumptions.
3. Step-by-step procedure.
4. How to verify the result.
5. Failure modes and troubleshooting.
6. Trade-offs, limitations, and references.

For a longer guide, split supporting chapters without creating a new platform:

```text
docs/posts/streaming-guide/
├── index.qmd             # Overview; listed in Writing
├── setup.qmd             # Linked from the overview
├── troubleshooting.qmd
└── img/
```

Each chapter needs its own YAML title and public-ready content. Link with source
paths such as `[Setup](setup.qmd)`; Quarto resolves the generated HTML path.
The current Writing pattern lists `index.qmd` files, so ordinary chapter
filenames do not become separate feed/listing entries.

Use callouts and diagrams instead of custom HTML where possible:

````markdown
::: {.callout-note}
## Assumption
These steps assume the stated broker and client versions.
:::

```python
# Displayed code: run and verify it in your development environment.
print("example")
```

```{mermaid}
flowchart LR
  Producer --> Broker --> Consumer
```
````

The public build does not execute your examples. Test them separately before
claiming they work.

## 5. Review a research paper

### Start from the reading template

```sh
mkdir -p drafts
mkdir drafts/lamport-clocks && \
  cp templates/paper-analysis.qmd drafts/lamport-clocks/index.qmd
```

Fill in the paper's identity/version, problem, contribution, method, evidence,
limitations, what you checked, and implications for your work. Distinguish:

- What the authors claim.
- What the reported evidence supports.
- Your interpretation or criticism.
- Any independent reproduction you actually performed.

Reading an abstract is not a full-text review. A public reading note is also
not the same as reviewing submissions for a journal or conference.

### Add real citations

Save a BibTeX export beside the note as `references.bib`, then add:

```yaml
bibliography: references.bib
```

For example, this is a real paper (metadata checked against its DOI record):

```bibtex
@article{lamport1978clocks,
  author = {Lamport, Leslie},
  title = {Time, clocks, and the ordering of events in a distributed system},
  journal = {Communications of the ACM},
  year = {1978},
  volume = {21},
  number = {7},
  pages = {558--565},
  doi = {10.1145/359545.359563}
}
```

Cite it with `[@lamport1978clocks]`. Verify both the bibliographic identity and
whether the source supports the sentence citing it. The build catches unresolved
citation keys; it does **not** validate your scientific interpretation.

Keep each document's bibliography local. The old global bibliography plugin is
not used. You can export selected references from a reference manager, but do
not link outside `docs/` to a personal library or restricted PDFs.

### Publish and index the note

Copy the reviewed bundle to `docs/reading/lamport-clocks/`, set `draft: false`,
and add a link in `docs/reading/index.qmd`:

```markdown
- [Lamport's clocks and event ordering](lamport-clocks/index.qmd)
```

Remove or revise the index's empty-state message as you add real content.

If the analysis is written as a chronological blog essay, `docs/posts/<slug>/`
is also valid. Link to that one canonical article from Reading instead of
maintaining two copies. The research agent currently uses this latter approach:
it produces `kind: paper-analysis` articles intended for `docs/posts/`.

## 6. Document projects and implement research ideas

### Keep an identifiable project at the center

For a project such as an exploratory streaming benchmark, use a stable identifier
like `streaming-benchmark` across its records. A useful relationship is:

```text
Contribution page: what I built and my role
    ├── Research report: question, method, evaluation, conclusion
    ├── Artifact repository: code, environment, data references, reproduction
    ├── Blog post: accessible explanation or tutorial
    ├── Publication record: venue/status, paper, citation
    └── Talk: slides, recording, transcript
```

These are different views of related work, not automatically separate inventions.
Do not create every page upfront. Start with one useful project record; add
other outputs as they actually exist.

### Project description

Copy [`templates/project.qmd`](templates/project.qmd) into a new draft folder.
After review, publish it at `docs/contributions/<project-id>/index.qmd` and link
it from `docs/contributions/index.qmd`.

Explain the problem, prior approaches, your specific contribution, implementation,
evaluation, reproduction, artifacts, external use where documented, and limitations.
For collaborative work, distinguish your role from the team's overall result.

### Original research idea and implementation

Use `docs/research/<project-id>/index.qmd` for the public research record. The
project template is a starting point; adapt its headings to the study:

| Stage | What to record |
| --- | --- |
| Idea | Question, motivation, prior work, assumptions, why the gap may matter |
| Protocol | Hypothesis or proof objective, baselines, metrics, data, failure criteria, planned analysis |
| Implementation | Code commit, environment, configuration, data version, hardware, seeds if relevant |
| Evaluation | Results, uncertainty, negative results, confounders, deviations from the protocol |
| Conclusion | What is supported, what is not, limitations, and next steps |
| Release | Versioned artifacts, reproduction commands, citation information, related paper/talk |

For theory work, use definitions, assumptions, proof steps, and counterexamples
rather than forcing an experimental template.

**The current agent does not implement or run your original experiments.** It
automates literature discovery and drafting. Run research code in an appropriate
research environment and bring verified outputs into the portfolio.

For substantial work, a separate repository is easier to reproduce and maintain.
A recommended structure—not something the site automatically creates—is:

```text
streaming-benchmark/        # Separate research repository
├── README.md
├── protocol.md
├── pyproject.toml
├── uv.lock
├── src/
├── tests/
├── experiments/            # Configurations and run instructions
├── analysis/               # Scripts/notebooks
├── results/                # Selected versioned results; large data stored elsewhere
└── reproduce.md
```

Do not make the portfolio's CI install every experiment's dependencies. Export
reviewed static plots/tables into the public page's assets and link to the exact
artifact commit or release. Record data checksums/versions and reproduction
commands in the artifact repository. Retain evidence needed to audit conclusions;
`.agent/runs/` is not the only durable record of a study.

A public exploratory note can have `draft: false` and `research-stage: exploratory`.
Say visibly that it is exploratory. Publication permission does not establish
correctness, novelty, or significance.

## 7. Add your publications and references

Use [`templates/publication.qmd`](templates/publication.qmd) for a **record of your
own work**, rather than a reading review of someone else's paper.

Publish the record at `docs/publications/<publication-id>/index.qmd`. Include:

- Exact title, author list, venue, date, and version.
- Explicit status: working note, preprint, accepted/published peer-reviewed work,
  or another accurately described artifact.
- Abstract or short summary and your contribution.
- DOI or other persistent paper link.
- Code, data/artifact links, project page, and related presentation.
- Verified BibTeX for readers who want to cite it.

Add a link to `docs/publications/index.qmd` and remove the empty-state language
when appropriate. Link the publication from its project/research page as well.
Do not imply peer review merely because an artifact has a DOI.

Use a professional profile to discover publications, then check the publisher,
DOI-registration metadata, or institutional/archive record. Prefer those records
when a profile's date, journal name, or link differs. Preserve complete author
order and the name used on each paper. Do not invent a DOI, coauthor role, or a
separate code release.

The populated records under `docs/publications/` provide examples: each has a
local `references.bib`, a rendered citation, and original-source links. A
`bibliographic-record-checked` evidence status means that the publication's
identity was checked, not that its findings were independently validated. Say
when a technical summary is based on an abstract rather than a full-paper review.

Keep dates at their known precision in the body and bibliography. A year-only
archive record does not justify an invented January 1 date in native `date`
metadata. Institutional rankings and publication counts also do not establish an
individual paper's impact.

### Three different uses of references

| Need | Where it belongs |
| --- | --- |
| Cite other work inside an article | The article's local `.bib` plus `[@key]` |
| List your own publications | A publication record and the Publications index |
| Maintain your personal reading library | A reference manager or appropriate private storage, not an automatically published resource folder |

Prefer a publisher, DOI, or authorized preprint link over copying a paper PDF
without redistribution rights. For your own permitted downloads, put the approved
PDF under that record's `assets/` and link it relatively.

Author manuscript PDF/LaTeX exports **outside** the public Quarto project, in the
manuscript/artifact workspace. The site's strict build accepts HTML only; it will
reject `format: pdf` or a mixed HTML/PDF declaration under `docs/`.

## 8. Connect talks, slides, and videos

Use [`templates/talk.qmd`](templates/talk.qmd), publish the record under
`docs/talks/<talk-id>/index.qmd`, and link it from `docs/talks/index.qmd`.

Record the event/date and accurately label an invited talk, submitted talk, or
self-published demo. Include recording, slides, transcript, and related projects.
YouTube embedding is supported with Quarto's video shortcode:

```markdown
{{< video https://www.youtube.com/watch?v=JHGOzwrlW8s >}}
```

Replace the existing demo URL with your actual recording. Keep large videos off
GitHub Pages. Speaker notes and draft transcripts need review before disclosure.

Render a separate RevealJS slides source outside `docs/`, then link to its hosted
release or approved PDF. Do not set `format: revealjs` on a public site page;
that page is the HTML landing record, not the slide-generation project.

## 9. Use the autonomous research framework

### Start with a local draft

```sh
uv sync --frozen --group agent
uv run --group agent python -m research_agent --help

uv run --group agent python -m research_agent \
  "How do streaming systems handle late events?" \
  --title "Late Events Literature Review" \
  --author raxit \
  --categories "Research,Distributed Systems" \
  --tags "Streaming" \
  --no-llm
```

`--no-llm` gives deterministic draft writing, but **retrieval still accesses the
network**. Omit it to use the configured model. Ollama requires its local service
and selected model; OpenAI requires the usual API credentials. For example:

```sh
export KIS_LLM_PROVIDER=ollama
export KIS_LLM_MODEL=llama3.1
```

These are configuration examples, not commands to install a model. Keep API keys
out of source files and Git history. Continue using `--group agent` in research
commands; a normal uv sync/run can otherwise remove the opt-in environment packages.

### Understand what a run produces

```text
.agent/runs/<run-id>/             drafts/<run-id>/<slug>/
├── candidates.json             ├── index.qmd
└── kept.json                   ├── <slug>.bib
                                └── assets/
                                    ├── sources.yml
                                    └── social.yml
```

The current pipeline is autonomous through:

```text
search → screen → synthesize → store → publish
```

By default, the final stage performs no Git/network publication. The article
remains a local draft. Metadata ranking is heuristic; the writer sees truncated
abstracts, not verified full-text evidence. Treat its output as a starting point
for your reading and synthesis, not a completed systematic review or experiment.

Review the sources and each consequential claim. Preserve honest AI-assistance
and evidence disclosures. Social copy is only a sidecar; nothing is posted to
social platforms automatically.

### Choose one publication route

**Manual, controlled route:** revise the generated bundle, then copy its reviewed
sources into the chosen public location and follow the normal PR workflow.
This is the simplest route for a draft you have already edited.

**Agent-created PR route:** add `--no-dry-run` to a research invocation only when
you intend to authorize local Git changes, a remote branch push, and PR creation.
It performs a **new run**, not publication of a previously edited draft.

Before that run:

- Finish/review existing tracked and staged work; unrelated untracked files block it.
- Have `gh` installed and authenticated, and a writable `origin` remote.
- Start on the intended PR base branch. The publisher uses the current branch
  as the base, creates `research/<slug>`, and leaves you on that research branch.
- Use a title whose derived slug has no existing article directory or research branch.

The PR contains `docs/posts/<slug>/index.qmd` and the exact generated sidecars.
Its editorial `draft` flag becomes false, but the unverified-content disclosure
remains. The agent does not merge or deploy. A reviewed merge to a deployment
branch is the release boundary; no second promotion is required.

There is currently no resume, `--publish-existing`, full-text retrieval, or
experiment-execution mode. On a partial publication failure, inspect the reported
branch/stage; do not blindly rerun and overwrite or discard existing work.

## 10. Extend the site and the agents

### Add pages before adding infrastructure

Most growth needs only a new `.qmd` bundle and an index link. For a new collection:

1. Decide whether an existing collection already fits.
2. Create its public `index.qmd` and reviewed content pages.
3. Link it from the appropriate index or `website.navbar` in `docs/_quarto.yml`.
4. Use existing supported metadata and local assets.
5. Run the strict build; test the page at the `/keep-it-simple/` subpath.

Changing `kind` alone does not select a folder, template, index, or navbar entry.
If you add a genuinely new scaffolder kind, update the allowed kinds in
[`tools/scaffold.py`](tools/scaffold.py), its template/CLI behavior as needed, and
tests. Do not create new kinds merely to represent a new category such as Kafka.

### Turn a curated collection into an automatic listing

This is an **optional future configuration change**, not current behavior.
For example, once real paper analyses exist, a Reading index could use:

```yaml
listing:
  contents: '*/index.qmd'
  sort: date desc
  categories: true
```

That pattern matches immediate child note directories, not the index itself.
If the collection can be empty, use the same empty-YAML-catalog pattern as
[`docs/writing/index.qmd`](docs/writing/index.qmd); unmatched listing paths cause
a warning and therefore fail the strict build. Adding a listing still does not
make research/publication statuses into rendered badges automatically.

For RSS on Writing, enable `listing.feed: true` only after content exists, build,
verify the generated feed, and then add a link to it. Keep publication dates stable.

### Change styling without adopting another frontend stack

The approved academic layout is **dark by default on a first visit**. An explicit
light/dark choice is remembered by Quarto. Keep `dark` before `light` in the theme
mapping; do not replace this with a script that resets the reader's choice.

The profile sidebar uses the native `website.sidebar` configuration. Edit its
`header` fenced Markdown block in `docs/_quarto.yml` and the image in
`docs/assets/profile.jpg`, and keep role/education details consistent with About/CV.
Keep the bio inline: Quarto 1.10.19 resolves header filenames relative to each
page, so a shared file path can turn into literal text on nested routes. Use
project-root-relative internal links such as `/about/index.qmd` in this shared
block. Its Markdown and HTML links remain subject to the public-path checks;
private-file references and active include shortcodes are still prohibited.

- Choose supported stock themes in `docs/_quarto.yml`.
- Make small changes in [`docs/stylesheets/extra.css`](docs/stylesheets/extra.css).
- Check both color modes and mobile layout.
- Use `uv run tests/browser_smoke.py` after building for the optional Chrome smoke check.

The strict authoring policy rejects custom filters/engines/hooks, file-based
custom themes, non-HTML output, and active shortcodes other than video. Do not
bypass it just to silence a warning. A new capability needs a deliberate policy
change in [`tools/validate_site.py`](tools/validate_site.py), regression tests, and
updated documentation. The checks reduce accidental publication risk; they are
not a general sandbox for arbitrary extensions.

### Extend your existing LangGraph framework incrementally

| Change you need | Start in |
| --- | --- |
| Another literature source | `research_agent/sources/`, returning the existing `Paper` model |
| New source/provenance fields | `research_agent/models.py` and `bibliography.py` |
| Better relevance/screening | `research_agent/credibility.py` and offline evaluation tests |
| New runtime options | `research_agent/config.py` and `__main__.py` |
| A new synthesis strategy | `research_agent/writing.py` |
| A new autonomous stage | `research_agent/graph.py`, preserving state contracts and downstream inputs |
| Different bundle content | `research_agent/artifacts.py` and shared scaffolding |
| Another model provider | `research_agent/llm.py` with optional dependencies |
| Publication changes | `research_agent/publish.py`, with isolated Git tests |

Start with a failing offline test, implement the smallest useful change, and
verify the real pipeline with controlled inputs:

```sh
uv run pytest -q
uv run --group agent pytest tests/test_graph_workflow.py -q
uv run ruff check .
uv run python -m tools.build_site
```

Retain autonomous progression between research stages and the human-reviewed
public release boundary. New experiment stages should run in an explicitly
chosen research environment—not in the website build. Never implicitly ingest
`.personal/`, credentials, or restricted manuscripts.

Add ordinary tooling dependencies with `uv add <package>`; optional research
packages with `uv add --group agent <package>`. Commit intentional changes to both
`pyproject.toml` and `uv.lock` after reviewing them. Quarto upgrades use
`.quarto-version` plus a matching local installation and render/test verification;
CI reads that version file.

## 11. Maintain the collection

### After each substantial result

- Update the canonical project/research record, not several inconsistent copies.
- Add dated results and limitations; retain negative findings when relevant.
- Link the exact released artifact version and reproduction instructions.
- Add publication or presentation records only when they exist.
- Record external use with sources rather than inferring impact from popularity alone.

### When updating a published article

Edit its existing source folder, retain its URL and original date, and add
`date-modified` with the actual revision date. Explain significant corrections
in an update note. Do not silently replace an exploratory claim with a stronger
conclusion without the supporting evidence.

If a URL must move, review incoming source links and
[`config/redirects.yml`](config/redirects.yml). Its helper handles directory-route
redirects such as `old-slug/: posts/new-slug/`; it refuses collisions with real
pages. These are static compatibility pages, not server-side HTTP 301 rules.

### Keep navigation useful

Curate Home around selected work. Use the collection indexes for complete lists.
Avoid adding every post to the top navbar. Periodically replace empty-state text,
check external paper/artifact links manually, and review About for outdated roles.
The strict build checks local links; it does not prove that external websites,
DOIs, videos, or downloads remain available.

Keep this handbook, the README, and AGENTS.md aligned when commands or workflows
change. This `AUTHORING.md` is repository documentation, not deployed site content.

## 12. Troubleshooting and a publishing checklist

| Symptom | What to check |
| --- | --- |
| `quarto` not found or wrong version | Install the version in `.quarto-version`, or use the documented local PATH / build `--quarto` option |
| Unknown author | Add the ID to `config/authors.yml`; native page metadata uses the person's display name |
| Draft rejected by strict build | Keep unfinished sources outside `docs/`; approved public content uses boolean `draft: false` |
| Post already exists | Edit the existing source or choose a different slug; do not overwrite to bypass a collision |
| Page renders but is not in its collection | Add the manual index link; only Writing is auto-listed today |
| Missing image/reference | Copy the actual asset/BibTeX, correct its relative path, and rebuild |
| Unresolved citation | Match the citation key to the declared local `.bib`; remove template/example keys |
| Reference escapes `docs/` | Publish an authorized copy inside the source bundle or link to a public external artifact; do not reference private/local folders |
| Preview works but strict build fails | The strict builder adds warning, format, path, draft, citation, and output checks |
| Empty listing warning | Ensure real content matches or retain an empty YAML catalog; do not create fake entries |
| Agent cannot import LangGraph/provider modules | Use `uv run --group agent ...`; the default environment intentionally omits heavy dependencies |
| Agent PR refused | Check staged/tracked/untracked state, current base branch, `gh` auth, and destination/branch collisions |
| Successful build but live site unchanged | Check source-branch deployment conditions and Actions; local rendering never publishes |

### Before each public release

- [ ] The content is authorized for public disclosure, including every asset/sidecar.
- [ ] Title, author, date, description, and status are accurate.
- [ ] Draft placeholders, sample citation keys, and nonexistent links are removed.
- [ ] Claims are backed by actual sources, results, or clearly labeled reasoning.
- [ ] Personal/team contributions and AI assistance are described honestly.
- [ ] Images, citations, and internal links work in the full site preview.
- [ ] The correct collection index links the page.
- [ ] `uv run python -m tools.build_site` passes.
- [ ] Tooling changes also pass tests and Ruff.
- [ ] The Git diff includes only intended sources—not generated HTML or ignored data.
- [ ] Publication happens through a reviewed source change and the existing CI.

**Sustainable habit:** one substantial piece of work, one canonical record,
clear supporting artifacts, and related explanations that link back to it.
