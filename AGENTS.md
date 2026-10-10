# Keep It Simple — Agent Guide

A **Quarto** engineering/research portfolio deployed to GitHub Pages, with an
optional **LangGraph autonomous research framework**. Quarto publishes content;
it does not replace the research framework or run experiments in site CI.

## Working agreements

- Start by reading [HANDOFF.md](HANDOFF.md) and [README.md](README.md), then inspect
  the current branch/index/worktree. Those files and this guide are the portable,
  public-safe project memory; do not depend on old chat transcripts or ignored plans.
- Keep README setup/authoring instructions, HANDOFF decisions/status/next steps,
  and this guide aligned with implemented behavior. Essential authoring guidance
  is consolidated in README; do not recreate the removed standalone handbook by default.
- Use **uv** for Python dependencies and commands. Quarto is a standalone CLI.
- Preserve existing user changes. Do not bulk-stage, reset, stash, commit, push,
  merge, or publish without the relevant authorization.
- Maintain truthful attribution and evidence status; do not invent research,
  publications, citations, awards, professional service, or impact metrics.
- Do not implicitly read or ingest `.personal/`. Never copy its content into
  tracked files, model prompts, generated articles, logs, or PRs.

## Commands

```sh
uv sync --frozen
quarto preview docs --port 8000 --no-browser
uv run python -m tools.build_site
uv run python -m tools.new_post
uv run pytest -q
uv run ruff check .
uv run ruff format .
uv sync --frozen --group agent
uv run --group agent python -m research_agent --help
uv run --group agent pytest tests/test_graph_workflow.py -q
```

- Python is pinned by `.python-version`; Quarto by `.quarto-version`.
- If using the ignored portable Quarto installation, put
  `.local/quarto/1.10.19/bin` on PATH for the current shell. Do not assume it is
  present in a fresh clone or on CI.
- `pyproject.toml` and `uv.lock` are authoritative for Python dependencies.
  Core dependencies support authoring, validation, and pure research models;
  `dev` supplies checks; the heavy `agent` group remains opt-in.
- `tools.build_site` is the strict public build. Always use it before considering
  public content complete. A successful preview or raw render is insufficient.
- Quarto integration tests may skip without the renderer; release verification
  must run with it available. Agent integration tests require the optional group
  but use controlled retrieval and no live LLM calls.

## Sources and generated outputs

- `docs/_quarto.yml`: the single authoritative public website configuration.
- `docs/`: only approved public content. Public routes use directory `index.qmd` files.
- `docs/contributions/`: project-oriented descriptions, roles, methods, artifacts,
  sourced use, and limitations. Existing projects are self-described engineering
  work, not automatically independently validated original contributions.
- `docs/research/`, `docs/reading/`, `docs/publications/`: distinct research,
  critical reading, and publication collections. Empty states are legitimate.
- `docs/posts/<slug>/index.qmd`: public articles. Colocate images and bibliography.
- `docs/writing/`: native article listing. `empty.yml` contains zero items and
  prevents a warning when no article exists; it is not a fake post.
- `docs/talks/`, `docs/about/`: real presentations/demo and professional profile.
- `docs/service/`, `docs/recognition/`, `docs/awards/`, `docs/memberships/`,
  `docs/media/`: visible professional-record collections. Keep empty states honest;
  never populate them with fictional achievements.
- `docs/_quarto.yml` → `website.sidebar.header`, `docs/assets/profile.jpg`:
  native sidebar bio/photo. Keep the bio as inline fenced Markdown; Quarto 1.10.19
  resolves header file paths relative to each page. Use project-root-relative
  internal links and keep role/education consistent with About/CV.
- `docs/_site/`: ignored generated public output; the only deployment artifact.
- `config/authors.yml`: author IDs/display metadata for tools and agents.
- `config/redirects.yml`: compatibility redirects from retired URLs.
- `templates/`: unpublished content templates; never part of site rendering.
- `drafts/`: ignored local draft bundles, separate from the public source tree.
- `HANDOFF.md`: committable engineering history, decisions, limits, and continuation
  steps. Keep it concise and free of private planning, credentials, or machine paths.
- `.agent/`: entirely ignored, including local plans, candidates, audits, and run
  scratch. Put durable shared decisions in HANDOFF, not only in this directory.
- `.superpowers/`, `.local/`, IDE state, and `.venv/`: ignored machine/session data.
- `.personal/`: ignored local personal knowledge, never a CI or public input.

There is no root Quarto project recursively rendering the repository. A private
local notebook can have its own ignored config with explicit render targets;
it must not become a dependency of the public build or fresh-clone tests.

## Fresh-machine continuation

- Install uv and Quarto from official distributions using the repository's pins;
  create a fresh environment with `uv sync --frozen`. Do not copy `.venv/` or assume
  the previous laptop's ignored portable Quarto binary exists.
- Clone the branch containing the user's committed **and pushed** work. Neither
  uncommitted changes nor local-only commits are available from a GitHub clone.
- Run the strict build, tests, and Ruff with Quarto on PATH. Install `--group agent`
  only for agent work; controlled agent tests need no live model or API credentials.
- Private notes, drafts, credentials, model downloads, and session logs do not
  clone. Any requested private transfer is separate and must not populate shared docs.
- Preserve the index and existing edits when preparing a commit candidate. Never
  interpret a readiness check as authorization to stage, commit, push, or deploy.

## Presentation and record placeholders

- The approved design is dark-first, inspired by information-rich academic
  profiles. Keep the `dark` theme first and preserve Quarto's remembered user choice.
- Use CSS and native Quarto navigation/sidebar features, not a separate frontend.
- Professional collections use `record-status: awaiting-entries` until actual
  records are added. Replace their `.collection-empty` block and change the status
  to `populated`; do not treat this as a scientific or legal qualification.
- `templates/professional-records.md` provides fill-in snippets outside the site.
  Remove all bracketed prompts before publishing an entry.
- Forked projects must retain upstream credit and distinguish the author's own
  contribution from the upstream implementation and results. A related authored
  thesis does not establish ownership of a fork's upstream code.
- Prefer publisher, DOI-registration, and institutional/archive records for
  publication identity, complete author order, venue, and date. Keep source-date
  precision; do not invent a day when only a year or month is known. The
  `bibliographic-record-checked` evidence status describes metadata verification,
  not peer review, independent reproduction, or validation of findings.
- University/employer rankings belong in clearly labeled institutional context
  under Recognition, not in personal awards or individual citation-impact claims.
- Keep private evidence planning out of the professional website and shared docs.

## Authoring

Use `uv run python -m tools.new_post` to create a native Quarto draft. It writes
`drafts/<slug>/index.qmd` and asset directories, refuses unknown authors/unsafe
paths, and does not overwrite unless explicitly requested.

- Native metadata includes `title`, `author`, `date`, `description`, `categories`,
  `kind`, `draft`, and `ai-assisted`.
- Source dates are not build dates. Do not silently refresh publication dates.
- Descriptions supply listing excerpts. Use `bibliography: file.bib` with
  `[@citekey]`, ordinary code fences, native math/callouts, and Mermaid.
- Keep kind, editorial state, research stage, publication status, and evidence
  status distinct. Do not promote a preprint to peer-reviewed via inference.
- For manually authored content, review the complete bundle before copying it
  into `docs/posts/<slug>/` and setting `draft: false`. Check destination collisions.
- Website source rejects `draft: true`; blanking a draft alone is not adequate
  protection against accidentally copied assets.
- Keep substantial experiments and optional manuscript/slide exports in their
  own environments. Publish reviewed output; do not install all experiment stacks
  to build a static site.

## Publication validation

`tools/documents.py` provides duplicate-key-rejecting YAML and native serialization.
`tools/site_config.py` provides shared identity and bounded filesystem paths.
`tools/validate_site.py` checks the supported source surface and generated links;
`tools/redirects.py` emits static redirects. `tools/build_site.py` coordinates
version checks, source validation, safe output cleaning, no-execute rendering,
warning handling, redirects, and output validation.

- No source symlinks or local file references escaping `docs/`. Sidebar header/footer
  and body/margin header/footer values accept checked fenced Markdown blocks or
  bounded local file references. Prefer inline blocks with project-root-relative
  links for shared content, so it renders at every depth. Include shortcodes stay disabled.
- Sensitive file names (`.env*`, key containers, credential/secret exports) and
  private/configuration directories are refused in public source and output,
  including unreferenced files and explicit resource copies. Safe environment
  templates may be committed outside `docs/` with placeholders only.
- These checks are not a secret-content scanner. Audit final Git candidates and
  history with a redacting scanner; never print detected credentials or send
  repository contents to an external scanning service.
- No custom filters/engines/execution hooks or file-based custom themes; use
  stock themes and CSS. Active shortcodes other than video are unsupported.
  Quarto's escaped shortcode syntax is available for literal examples.
- The guard is not a sandbox for arbitrary hostile extensions.
- Force HTML-only public renders and require an actual homepage in the output.
  Export other formats separately. A zero exit without files is not success.
- Validate internal links/ordinary fragments, assets, citations, search, feeds,
  sitemap, canonical URLs, and the publication boundary.
- Do not suppress warnings to pass a build. Resolve the source or add a narrow,
  justified compatibility rule with regression coverage.
- Only the exact owned `docs/_site/` can be cleaned; do not follow output symlinks.

## Autonomous research framework

Retain `research_agent/`, its source adapters/models/provider abstraction and
five-stage flow: search → screen → synthesize → store → publish. No new human
approval prompts between stages. Improve this framework incrementally rather
than replacing it with a skills package or a manual writing workflow.

- `KIS_LLM_PROVIDER` and `KIS_LLM_MODEL` remain supported (Ollama/OpenAI).
- `--no-llm` affects writing only; retrieval can still access the network.
- Default dry run emits an unverified Quarto bundle outside `docs/`, with no Git
  or remote operations. Each run is unique and existing bundles are protected.
- Metadata heuristics and truncated abstracts are not full-text research validation.
- `--no-dry-run` can prepare a site change on `research/<slug>` and open a PR.
  A reviewed merge is the release gate; no second manual promotion is required.
- Publication validates an exact nonsymlink bundle, checks Git/auth before
  mutation, scopes commits to generated site files, and never merges or deploys.
  Partial failures preserve files/branches and report the reached stage.
- Generated social copy is a sidecar, not automatic social posting.

## GitHub Pages

The public base is `https://raxit65535.github.io/keep-it-simple/`. Preserve the
project subpath in all links, redirects, feed entries, and social/canonical URLs.

`.github/workflows/ci.yml` validates with read-only permissions. A separate job
publishes the validated artifact to the existing `gh-pages` branch only for
`main`/`release` pushes or permitted manual dispatch. Feature branches and PRs
never deploy. Superseded same-ref runs are canceled, with deployments serialized
across refs. The deploy step does not re-render. No notebook or model runs in CI.

Do not run `quarto publish`, change Pages settings, or push as a setup shortcut.
The existing remote branch is discoverable by Quarto; no initial local publish
is needed. Check the hosted site only after an authorized deployment.
