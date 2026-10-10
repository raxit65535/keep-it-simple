# Engineering handoff

Last updated: **2026-10-10 (UTC)**. This is public-safe project memory, not a
transcript or a store for private notes. Keep it current when behavior or
decisions change.

## Start here on another machine

1. Read [AGENTS.md](AGENTS.md) for working rules and [README.md](README.md) for
   fresh-laptop setup, authoring, verification, and publishing instructions.
2. Inspect `git status --short`, `git branch --show-current`, and recent
   history. Do not assume the checkout matches a previous session's branch or
   index.
3. Install the pinned Quarto CLI and use `uv sync --frozen`; run the strict
   build, tests, and Ruff before developing. No private/session directories are
   required.
4. Work from the current code and the decisions below. Ignored `.agent/` plans
   and `.superpowers/` sessions are optional local scratch, not prerequisites.

This preparation was performed on `raxit65535/eng-framework`. Changes must be
pushed before a GitHub clone on another laptop can contain them. The security
audit below accompanied user-authorized progressive local commits of the
migration. No push, merge, or deployment was performed; verify actual
Git/Actions state rather than treating this document as proof of publication.

## What has been implemented

### Quarto migration and build

- The public website is the Quarto project at `docs/_quarto.yml`, rendering only
  public sources under `docs/` into the ignored `docs/_site/` directory.
- Python **3.13** and Quarto **1.10.19** are pinned in `.python-version` and
  `.quarto-version`. Python dependencies are declared in `pyproject.toml` and
  locked in `uv.lock`.
- Active MkDocs/mise configuration and the original two starter posts were
  removed. Do not restore `requirements.txt` or introduce a second publishing
  stack.
- `tools.build_site` validates source, checks the renderer version, cleans only
  the owned output directory, forces non-executing HTML rendering, rejects
  warnings, writes compatibility redirects, and validates generated artifacts.
- Old post/tag/category/archive URLs have static redirects managed through
  `config/redirects.yml`. The project URL prefix remains `/keep-it-simple/`.
- GitHub Pages still uses the existing `gh-pages` branch. CI validates PRs with
  read-only permissions and deploys the validated artifact only for allowed
  `main`/`release` pushes or manual dispatches. It does not re-render at
  deployment.

### Academic profile and public records

- The approved design is content-rich and dark-first, with a remembered native
  light/dark toggle. It takes organizational cues from Andrew Heiss and Emi
  Tanaka, without replacing Quarto with a frontend framework.
- The profile photo, project diagrams, responsive layouts, and
  professional-record navigation are implemented. The sidebar bio is inline
  fenced Markdown in `website.sidebar.header`: the pinned renderer resolves
  header filenames relative to each page, which previously displayed a filename
  on nested routes.
- Home, Research, Projects, About/CV, Writing, Publications, Talks, Service,
  Recognition, Awards, Memberships, and Media remain discoverable. Empty
  sections are explicitly empty, not fabricated achievements.
- Five authored publication records are under `docs/publications/`, with full
  author attribution, source links, local BibTeX, and rendered citations:
  - _Git-Archive Data Pipeline_ — thesis, 2019.
  - _Prediction of Crop Cultivation_ — IEEE CCWC, 2019.
  - _Study of Distributed Framework Hadoop and Overview of Machine Learning
    using Apache Mahout_ — IEEE CCWC, 2019.
  - _Online Examination Empowerment_ — IRJET, July 2016.
  - _Accustoms of IOT and Security Concerns_ — IRJET, July 2016.
- Publication metadata was checked against ProQuest, IEEE's Crossref deposits,
  and publisher PDFs/archives. The publisher dates _Online Examination
  Empowerment_ to 2016, despite a different year on the professional profile.
  The IEEE/thesis technical summaries are not new full-text reviews or
  reproduced experiments.
- CSUF's reported citation-impact ranking is labeled institutional context, not
  a personal award or an individual citation-impact claim.
- UMatch and the research-workflow project have substantive case-study pages.
  The Network Pulse/Git Archive and batch-recommendation repositories remain
  credited as forks; an authored thesis does not establish ownership of upstream
  code.

### Authoring and research framework

- `uv run python -m tools.new_post` creates a Quarto draft outside the public
  site at `drafts/<slug>/index.qmd`, with asset folders and explicit draft
  metadata. `config/authors.yml` is the author registry.
- Only Writing is automatically listed. Other collection indexes require curated
  links to child records. Templates cover papers, projects, publications, and
  talks; there is no general new-project or promotion CLI.
- Native citations, Markdown callouts, math, Mermaid, local assets, search, and
  social metadata are available. Public builds are HTML-only and disable
  computation.
- The retained LangGraph flow is **search → screen → synthesize → store →
  publish**. The heavy `agent` dependency group is optional and is not installed
  for site CI.
- The provider/model are configurable with `KIS_LLM_PROVIDER` and
  `KIS_LLM_MODEL`. Default dry runs write ignored drafts and scratch. `--no-llm`
  skips model writing, not network retrieval. `--no-dry-run` starts a new run
  and can open a reviewed site PR; it never merges or deploys, and there are no
  added approval pauses between stages.
- The publisher validates an exact bundle, checks Git/auth state before
  mutation, scopes commits to generated site files, refuses unrelated
  work/destination collisions, and reports partial failures without discarding
  files.

### Security and portability hardening

- `.gitignore` excludes private notes, all local agent plans/runs, session
  artifacts, machine-local tools, environments, IDE state, drafts, generated
  output, and common credential/key files. Placeholder-only environment
  templates can remain outside `docs/`.
- Sidebar header/footer and body/margin header/footer imports are now subject to
  the same public-path checks. Checked inline fenced Markdown is supported for
  shared content without page-relative file-path assumptions.
- Sensitive filenames and private/configuration directories are rejected in
  public source and output, including unreferenced files and explicit resource
  copies. This closes the demonstrated footer-import and `.env.local`-resource
  leaks.
- `tests/test_privacy_guards.py` uses synthetic data to cover these boundaries.
  `tests/test_ignore_policy.py` tests actual Git ignore behavior independently
  of the developer's global Git configuration.
- These are publication-boundary and filename guards, not a general sandbox or
  secret-content detector. A credential pasted into an ordinary-looking article
  still requires content review and a redacted secret scan.

## Where to change things

| Concern                                      | Main files                                                                                                 |
| -------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| Website navigation, profile bio, theme       | `docs/_quarto.yml`, `docs/stylesheets/extra.css`                                                           |
| Public content and collection links          | `docs/` collection indexes and child `index.qmd` files                                                     |
| Authoring examples and record structure      | `templates/`, README authoring sections                                                                    |
| Metadata parsing and site identity           | `tools/documents.py`, `tools/site_config.py`                                                               |
| Publication boundaries and strict build      | `tools/validate_site.py`, `tools/build_site.py`, `tools/redirects.py`                                      |
| Draft scaffolding                            | `tools/scaffold.py`, `tools/new_post.py`                                                                   |
| Research pipeline, retrieval, and synthesis  | `research_agent/graph.py`, `research_agent/sources/`, `research_agent/writing.py`, `research_agent/llm.py` |
| Draft artifacts and optional PR creation     | `research_agent/artifacts.py`, `research_agent/publish.py`                                                 |
| Deployment                                   | `.github/workflows/ci.yml`                                                                                 |
| Portable instructions and engineering memory | `README.md`, `AGENTS.md`, `HANDOFF.md`                                                                     |

## Decisions to preserve

- Keep Quarto as the publishing layer and LangGraph as the optional research
  tool. Do not turn static site builds into notebook/model/experiment runs.
- Use uv and the committed lockfile. Install Quarto separately at the pinned
  version. The old laptop's ignored portable binary is not a dependency of the
  repository.
- Preserve dark-first behavior, accessibility checks, native navigation, and the
  reader's explicit theme choice. Keep new content factual rather than filling
  collections with invented accomplishments.
- Keep publication status, research stage, editorial draft state, and evidence
  status distinct. Preserve exact author order, source-date precision, and fork
  credit.
- Only `docs/_site/` is the deployment artifact. Private directories must not
  become inputs to public pages, prompts, test fixtures, CI artifacts, or shared
  plans.
- Do not force-add ignored private files or stage unrelated changes. Never infer
  authorization to commit/push/deploy from a build or readiness request.
- `AUTHORING.md` was intentionally left deleted during this preparation.
  Essential guidance is now in README, AGENTS, this handoff, and the existing
  templates.

## Known limits and useful next work

- The research writer uses truncated abstracts and metadata heuristics; it is
  not a full systematic-review, scientific-validation, or experiment-execution
  system.
- There is no resume/publish-existing agent mode, automatic promotion CLI, or
  automatic listing for collections other than Writing. Add these only for a
  clear need.
- Original experiments and any independent impact evidence must be produced and
  documented separately. Bibliographic verification does not establish those
  results.
- Review About/CV for current role information and disclosure permissions. Some
  employment details came from the provided CV because the public profile hides
  them.
- Check the hosted site only after an authorized deployment; local verification
  does not mean GitHub Pages has changed. Both `main` and `release` target the
  same site.
- Repeat secret and dependency audits before substantial releases. Continuous
  secret scanning/action-SHA pinning are possible hardening work, not currently
  claimed as implemented CI features.
- Any private notes or unfinished drafts needed on another laptop require a
  separate secure transfer. Do not restore them from this document or add them
  to Git.

## Verification record

Verification reviewed on **2026-10-10 (UTC)**, on macOS ARM64 with Python 3.13
and Quarto 1.10.19:

| Check                            | Result                                                                                                                               |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Clean source-only copy           | 115 proposed Git-candidate files; no private/session directories or copied local tools                                               |
| Fresh default environment        | `uv sync --frozen`, strict build, and Ruff passed; **206 tests passed, 1 optional-agent module skipped**                             |
| Fresh optional-agent environment | Agent installation and CLI help passed; **208 tests passed** with controlled retrieval and no live model calls                       |
| Privacy regressions              | Previously leaking footer/file-resource fixtures now fail validation before rendering                                                |
| Secret scans                     | Gitleaks 8.30.1 reported no matches in the source candidate, original index, locally available history, or generated public artifact |
| Dependency audit                 | pip-audit reported no known vulnerabilities in 63 audited packages from the locked all-groups export                                 |

The clean copy used a new virtual environment and an empty temporary Git context
for ignore tests. It did not use the real repository's index, private notes,
credentials, old environment, or ignored agent memory. Quarto was supplied as an
externally installed tool, just as it must be on the new laptop. This is a
clean-source rehearsal on the current machine, not a claim that another physical
laptop or every OS has been tested.

The earlier clean-source rehearsal did not stage, commit, push, or deploy.
Secret/dependency scans are point-in-time checks, not a guarantee against every
kind of sensitive content or future vulnerability. Repeat verification on the
final reviewed commit candidate and after changes on the new machine.

### Pre-commit security recheck

On **2026-10-10 (UTC)**, the current migration was checked again before making
user-authorized local commits:

- Gitleaks **8.30.1**, with full redaction, reported no matches in the
  Git-visible source candidate, original index, locally available Git history,
  or freshly generated `docs/_site/` artifact. Each staged commit candidate was
  also scanned.
- History scanning covered local branches, remote-tracking refs, and the stash;
  no remote fetch or hosted-site check was performed. Private `.personal/` paths
  were excluded, and ignored private/session content was not ingested.
- With Quarto **1.10.19** available, the optional-agent suite passed **208
  tests**; Ruff and the strict public build passed. Agent tests used controlled
  retrieval and no live model calls.
- Progressive commits separate ignore-policy protection, the Quarto/research
  migration, and shared setup/handoff documentation. No push or deployment is
  authorized by this audit.

No credential exposure was detected within the scanned surfaces. This is not
proof that all sensitive information is absent: pattern scanners do not replace
disclosure review, and unavailable remote history was not scanned. The prior
dependency-audit result above was not rerun during this secret-focused recheck.
