# Professional record snippets

Authoring templates only. Copy one section into an appropriate draft or collection
index, replace every bracketed field, verify sources and permissions, and remove
unused fields before publication. Do not publish these example placeholders.

When adding the first real record to an empty collection:

1. Replace the `.collection-empty` block with the reviewed entry or a link to it.
2. Set `record-status: populated` in that index's front matter.
3. Keep `draft: false` only for the content approved for disclosure.
4. Add any necessary parent-index link and run the strict build.

These snippets do not introduce new scaffolder `kind` values. For papers and
projects, use [publication.qmd](publication.qmd) and [project.qmd](project.qmd).

## Reviewing and service

```markdown
## [Activity or venue]

- **Organization / venue:** [Name]
- **Role:** [Reviewer, committee member, evaluator, or another exact role]
- **Period:** [Dates]
- **Status:** [Invited / completed / currently serving, as documented]
- **Contribution:** [What you actually did; avoid confidential submission details]
- **Public confirmation:** [Authorized source URL, if available]

[Brief context and any relevant limits on what can be disclosed.]
```

Destination: `docs/service/index.qmd` or a linked record under `docs/service/`.
Do not publish manuscripts, review text, or private correspondence without permission.

## Award or honor

```markdown
## [Award or honor name]

- **Granting organization:** [Name]
- **Date:** [Actual award date]
- **Recipient:** [Individual or team; identify your role accurately]
- **Recognition basis:** [What was recognized and any documented selection context]
- **Related work:** [Project/publication link]
- **Source:** [Official announcement or authorized supporting record]
```

Destination: `docs/awards/index.qmd` or a linked record under `docs/awards/`.
Do not substitute an employer's award for an individual award without explanation.
University/employer rankings belong in a separately labeled institutional-context
section under `docs/recognition/`, not in the personal-awards collection. Preserve
the report date, exact metric, and original source.

## Professional membership

```markdown
## [Organization]

- **Membership grade / position:** [Exact designation]
- **Period:** [Dates]
- **Selection or eligibility basis:** [Documented information, if relevant]
- **Participation:** [Activities actually performed]
- **Source:** [Official organization/profile link, when publicly available]
```

Destination: `docs/memberships/index.qmd` or a linked record under `docs/memberships/`.
Do not imply a selective grade or active service from ordinary membership alone.

## Media and external coverage

```markdown
## [Title of coverage]

- **Publication / outlet:** [Name]
- **Author / interviewer:** [Name]
- **Date:** [Publication date]
- **Type:** [Editorial coverage / interview / sponsored material / other]
- **Work discussed:** [Specific project or contribution]
- **Original source:** [URL]

[Short factual description; quote only what is appropriate and permitted.]
```

Destination: `docs/media/index.qmd` or a linked record under `docs/media/`.
Keep self-authored posts in Writing; do not relabel them as independent coverage.

## Contribution or experience update

```markdown
### [Specific contribution or responsibility]

- **Your role:** [Personal work, distinguished from the team's work]
- **Context:** [Organization/project and relevant dates]
- **Outcome:** [A bounded factual statement]
- **Supporting record:** [Authorized evidence or public artifact]
- **Limitations:** [What the evidence does not establish]
```

Use this within an existing project/research page or `docs/about/index.qmd`.
Preserve upstream attribution for forks and collaborators. Compensation records,
confidential letters, and sensitive supporting documents do not belong in public
pages or in these shared templates.
