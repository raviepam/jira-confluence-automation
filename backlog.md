# Project-Specific PR Reviewer Backlog

## Planning Notes

- **Session closeout rule:** At the end of each work session, update this backlog to mark completed work, record current progress and blockers, and add or reprioritize newly discovered tasks. Keep checkboxes aligned with verified implementation status.
- **Phase order:** Strictly follow Setup, Core Features, Integration, Testing, then Documentation. Do not begin a later phase until the prior phase's exit criteria are accepted.
- **Initial priority:** Establish authenticated GitHub PR intake and versioned repository guidance/context before expanding review behavior.
- **Initial release:** Advisory only. Do not block merges or apply code changes. Keep inline-comment mode disabled until the Testing phase's release gate passes.
- **Sizing:** Epic/story-sized work items; each checkbox describes a reviewable deliverable. Split into team tickets as owners and implementation details are assigned.
- **Unknowns:** The approved private model, actual PR volumes, retention limits, quality thresholds, pilot repositories, and shadow-mode presentation require stakeholder decisions in Setup. Values called provisional in `project_spec.md` must not be treated as commitments.
- **Execution labels:** `MCP` means the task's primary operation needs authenticated live access to an external system through an MCP server or approved API connector. `custom skill` means repo-local code, analysis, tests, or documentation can carry out the work; a skill may invoke MCP when it needs external data. Labels identify the primary execution path, not exclusive tooling. The current workspace does not configure GitHub, cloud, or model MCP servers, so those connections are setup dependencies.
- **Execution labels:** `MCP` marks work whose primary path requires live access to GitHub, the approved model, or cloud services. `custom skill` marks repo-local implementation, analysis, testing, or documentation. A skill may orchestrate MCP calls, but implementing or testing an MCP server remains custom-skill work; human approvals remain human decisions.

## Decisions Made

### Confirmed

- **Source control integration:** Target GitHub Enterprise Cloud, with PR events and CI/check workflow support.
- **Initial technology scope:** TypeScript/Node.js and Terraform, Kubernetes, and Helm.
- **Review scope:** Analyze the full PR and affected dependencies; anchor findings to relevant changed lines.
- **Repository context:** Use versioned YAML guidance in each repository, along with architecture docs/ADRs and API schemas/contracts.
- **Initial domain:** Focus commerce-specific rules on orders, refunds, and cancellations.
- **Review priorities:** Security/privacy, distributed reliability, actionable maintainability risks, and test/operability risks.
- **Finding quality:** Emit only concrete, actionable findings with severity, confidence, rationale, and changed-line citations; suppress duplicates and speculative style-only feedback.
- **Model/data boundary:** Use an approved enterprise model hosted in company cloud/private network; do not send source code to public model endpoints. Redact secrets and PII before model requests and audit reviews/config changes.
- **Autonomy:** Advisory only for the initial release; do not block merges or autonomously modify code.
- **Rollout:** Pilot selected teams/repositories in shadow mode before enabling inline comments. Comment enablement requires verified security/privacy controls, shadow-pilot evidence, a measured quality threshold, and commerce-domain-owner approval.
- **Planning:** Keep the phases in strict order: Setup, Core Features, Integration, Testing, Documentation. Prioritize authenticated GitHub intake and repository policy/context first.

### Proposed; validate in Setup

- **Service topology:** Webhook/API service, queue, workers, context/policy loader, redaction layer, model adapter, finding validator, publisher, and audit/metrics store.
- **Repository config path:** `.pr-reviewer.yml` is proposed; confirm the path and schema during Setup.
- **Shadow output:** A non-blocking CI check/artifact is proposed; confirm the preferred visibility with pilot teams.
- **Operational targets:** The 5-minute p95 review completion and 99.5% monthly availability values in `project_spec.md` are provisional until actual load and service objectives are agreed.

## Phase 1: Setup

**Exit criteria:** Pilot scope, security boundaries, service contracts, repository policy format, infrastructure prerequisites, and evaluation method are approved.

- [ ] **S-01 (P0) [custom skill] Confirm pilot scope and operational constraints.** Select pilot repositories and owners; inventory TypeScript/Node.js and Terraform/Kubernetes/Helm usage; record expected PR volume, peak concurrency, diff sizes, residency, retention, and availability requirements. Capture unresolved answers as decisions, not assumptions.
- [ ] **S-02 (P0) [custom skill] Approve the service architecture and trust boundaries.** Document GitHub App, webhook/API, queue, workers, context loader, redaction, private-model adapter, finding validator, publisher, and audit/metrics store. Identify which components can access source and which can reach the model endpoint.
- [ ] **S-03 (P0) [custom skill] Define GitHub App permissions and installation policy.** Specify minimum read permissions for PRs/content and narrowly scoped check/comment write permissions; define allowed organizations/repositories, webhook events, credential storage, rotation, and uninstall behavior.
- [ ] **S-04 (P0) [custom skill] Define the repository YAML contract.** Specify the proposed `.pr-reviewer.yml` schema, schema versioning, organization defaults, repository overrides, policy precedence, required fields, path exclusions, and behavior for invalid/missing configuration. Prohibit repository overrides of mandatory security/model controls.
- [ ] **S-05 (P0) [custom skill] Select approved model and data-handling policy.** Obtain security/privacy approval for the private enterprise endpoint, authentication, data-processing terms, network route, allowed payload, retention/deletion, and model/version audit fields.
- [ ] **S-06 (P0) [MCP] Provision non-production foundations.** Define and provision isolated service environments, private networking, managed secrets, queue, minimal metadata store, encrypted storage, deployment pipeline, and access controls; verify source content is not written to ordinary logs.
- [ ] **S-07 (P0) [custom skill] Define evaluation and comment-release policy.** Select reviewers to label findings; define severity/confidence rubric, actionability and false-positive measurements, duplicate/line-anchoring measures, and how shadow results will be reviewed. Set numeric comment-enablement thresholds using stakeholder approval and pilot evidence.
- [ ] **S-08 (P1) [custom skill] Define service contracts and error semantics.** Specify versioned webhook job, review result, finding, audit event, and check/comment publisher interfaces, including timeouts, retryable errors, maximum payload sizes, and non-blocking behavior.

## Phase 2: Core Features

**Exit criteria:** Core services operate behind replaceable GitHub/model adapters, apply repository policy and redaction, and produce validated, deduplicated findings without requiring live external integrations.

- [ ] **C-01 (P0) [custom skill] Create the typed service skeleton.** Add application configuration, structured error handling, health/readiness endpoints, request/job correlation IDs, dependency injection, and CI lint/type-check/build commands.
- [ ] **C-02 (P0) [custom skill] Implement authenticated webhook intake.** Verify GitHub webhook signatures using constant-time comparison, reject invalid or stale deliveries, authorize the installation/repository, accept only configured PR events, and acknowledge valid events quickly after enqueueing.
- [ ] **C-03 (P0) [custom skill] Implement review-job lifecycle and idempotency.** Key jobs by repository, PR number, and head SHA; make webhook retries safe; supersede obsolete head revisions; track queued/running/succeeded/partial/failed states; bound retry count and execution time.
- [ ] **C-04 (P0) [custom skill] Implement repository configuration loading.** Parse and validate `.pr-reviewer.yml` against the approved schema; pin configuration to the reviewed commit; merge it with organization defaults; enforce mandatory policy; provide actionable diagnostics and safe fallback behavior.
- [ ] **C-05 (P0) [MCP] Implement bounded PR context collection.** Define an adapter contract and collect the diff plus required surrounding files at the exact head SHA; resolve configured ADRs, API schemas/contracts, and bounded affected-dependency context; skip excluded/generated/oversized files with an explicit partial-review reason.
- [ ] **C-06 (P0) [custom skill] Implement secret and PII redaction.** Redact detected credentials and configured sensitive values from code, comments, and documents before model submission; preserve line mapping where possible; emit redaction metadata without logging the values; stop model submission if redaction cannot run safely.
- [ ] **C-07 (P0) [MCP] Implement the private-model adapter contract.** Define timeouts, bounded retries, response-size limits, model/version reporting, structured input/output, and a test stub. Reject public or repository-configured model endpoints; leave production credentials and endpoint selection to approved deployment configuration.
- [ ] **C-08 (P0) [custom skill] Implement review orchestration and instruction isolation.** Supply only necessary, redacted context and applicable policies; treat repository content as untrusted data; prevent content from changing system rules, accessing tools, or requesting secrets; request evidence-backed candidate findings in a versioned schema.
- [ ] **C-09 (P0) [custom skill] Implement finding validation and changed-line mapping.** Validate required category, severity, confidence, title, impact, rationale, evidence, file, and line fields; reject unsupported locations and malformed output; map inline positions to changed lines; suppress below-threshold or duplicate findings.
- [ ] **C-10 (P0) [custom skill] Implement commerce policy inputs.** Represent owner-approved order, refund, and cancellation invariants in repository guidance; cover idempotency, duplicate/retried operations, invalid state transitions, authorization, and cross-service consistency only where supported by documented contracts.
- [ ] **C-11 (P0) [MCP] Implement result and comment lifecycle abstraction.** Define stable finding keys and interfaces to create/update/resolve prior findings idempotently; implement a no-op/test publisher and a mode switch for shadow versus inline-comment behavior; default to shadow/no comments.
- [ ] **C-12 (P0) [custom skill] Implement privacy-aware audit and metrics.** Record review ID, repository/PR/head SHA, event, configuration/prompt/model versions, outcome, timings, retry counts, and result identifiers. Exclude raw source, secrets, and unnecessary PII; apply access controls and configured retention.
- [ ] **C-13 (P1) [custom skill] Implement review limits and partial-result reporting.** Enforce configured limits for file count, diff size, context tokens, runtime, retries, and per-repository concurrency; return a clear partial/skipped status instead of silently omitting analysis.

## Phase 3: Integration

**Exit criteria:** A selected pilot repository can submit a real PR event, receive a revision-pinned shadow result using the approved private model, and publish feedback through the approved GitHub surface; inline comments remain feature-gated.

- [ ] **I-01 (P0) [MCP] Register and install the GitHub App in the pilot organization.** Configure approved webhook URL/events and minimum permissions; store credentials in the managed secrets service; verify installation and repository allow-list behavior.
- [ ] **I-02 (P0) [MCP] Connect GitHub event intake to the job pipeline.** Deliver signed test and live PR events through webhook verification, enqueueing, deduplication, status tracking, and bounded retries; confirm the webhook responds within the agreed intake objective.
- [ ] **I-03 (P0) [MCP] Integrate GitHub PR and repository APIs.** Fetch the PR diff, changed files, required contents, commit/head SHA, and relevant metadata through the installation token; verify permission failures, pagination, rate limits, file exclusions, and revision consistency.
- [ ] **I-04 (P0) [MCP] Connect the approved private enterprise model.** Configure private endpoint routing and managed credentials; verify TLS, endpoint allow-list, model/version recording, timeout/retry behavior, and that no request reaches a public model endpoint.
- [ ] **I-05 (P0) [MCP] Publish shadow-mode results.** Create/update a non-blocking GitHub check (and agreed artifact/details surface) with summary counts, findings, skipped/partial reasons, and run metadata; confirm it never posts inline comments or blocks merges.
- [ ] **I-06 (P1, gated) [MCP] Integrate inline review comments.** Implement changed-line comments and update/resolve behavior behind an organization-controlled feature flag; keep disabled until Testing release criteria and domain/security approvals pass.
- [ ] **I-07 (P0) [MCP] Deploy the pilot service.** Deploy API, queue, workers, configuration, secrets, and telemetry into the approved private environment; configure least privilege, autoscaling limits, health checks, alert routing, and rollback procedure.
- [ ] **I-08 (P0) [MCP] Onboard selected pilot repositories in shadow mode.** Add validated repo configuration and approved context references, confirm ownership/opt-out path, and run an end-to-end PR without enabling comment or merge-gating permissions.

## Phase 4: Testing

**Exit criteria:** Functional, security/privacy, resilience, quality, and operational results are reviewed; inline comments remain disabled unless all agreed release gates pass.

- [ ] **T-01 (P0) [custom skill] Test configuration and policy behavior.** Cover valid/invalid YAML, version compatibility, organization/repository precedence, missing-file defaults, immutable mandatory controls, excluded paths, and diagnostics.
- [ ] **T-02 (P0) [custom skill] Test webhook authentication and job idempotency.** Cover valid/invalid signatures, replayed deliveries, unauthorized installations/repositories, unsupported events, duplicate events, changed head SHAs, retries, and superseded jobs.
- [ ] **T-03 (P0) [custom skill] Test context collection and line mapping.** Use fixtures for binary/generated/large files, pagination, renamed/deleted files, missing context, API rate limits, and stale head SHAs; verify findings map only to valid changed lines.
- [ ] **T-04 (P0) [custom skill] Test redaction and prompt-injection resistance.** Seed known secrets and PII in source, comments, and docs; assert they do not appear in outbound model payloads or ordinary logs. Test adversarial repository instructions and verify system policy remains authoritative.
- [ ] **T-05 (P0) [custom skill] Test model and finding contracts.** Cover timeouts, malformed/oversized responses, unsupported claims, invalid severity/confidence, duplicate findings, low-confidence suppression, and graceful provider failure.
- [ ] **T-06 (P0) [MCP] Run end-to-end GitHub shadow tests.** Exercise PR opened/synchronize/reopened events through result publication; verify one result per head SHA, no inline comments, no merge blocking, and safe reruns.
- [ ] **T-07 (P0) [custom skill] Evaluate against a labeled PR corpus.** Include clean changes and seeded security/privacy, reliability, API compatibility, and order/refund/cancellation risks across supported stacks; report precision/actionability, false positives, severity calibration, duplicates, line anchoring, and category coverage.
- [ ] **T-08 (P0) [custom skill] Run resilience and load tests.** Simulate GitHub/model/queue outages, rate limits, worker restarts, retries, and bursty PR load. Compare latency, concurrency, and availability with targets confirmed in Setup; verify failures remain non-blocking to merges.
- [ ] **T-09 (P0) [custom skill] Complete security, privacy, and operational review.** Review threat model, permissions, network boundaries, secret management, retention/deletion, audit access, prompt injection controls, dependency scanning, and redaction limitations; track and resolve release-blocking findings.
- [ ] **T-10 (P0) [MCP] Review shadow-pilot evidence and decide comment gate.** Obtain selected-team, security/privacy, and commerce-domain-owner approval; verify redaction, documented domain invariants, and the measured quality threshold agreed in Setup. Record go/no-go and outstanding risks.
- [ ] **T-11 (P1, gated) [MCP] Verify inline-comment rollout.** If T-10 passes, enable comments for opt-in pilot repositories only; test permissions, changed-line anchors, duplicate suppression, updates/resolution, disable/rollback, and confirm no merge-gating behavior.

## Phase 5: Documentation

**Exit criteria:** Engineers, repository owners, operators, and security reviewers can configure, use, troubleshoot, and govern the pilot using reviewed documentation.

- [ ] **D-01 (P0) [custom skill] Publish architecture and data-flow documentation.** Document components, trust boundaries, webhook-to-model flow, data classifications, redaction placement, private endpoint routing, storage, audit, and retention decisions.
- [ ] **D-02 (P0) [custom skill] Publish repository configuration reference.** Document `.pr-reviewer.yml` schema, examples for TypeScript/Node.js and infrastructure repositories, domain-policy conventions, validation errors, policy precedence, exclusions, and safe override limits.
- [ ] **D-03 (P0) [custom skill] Publish installation and deployment guide.** Document GitHub App setup/permissions, environment configuration, private networking, managed-secret setup/rotation, deployment, feature flags, and rollback steps without including secret values.
- [ ] **D-04 (P0) [custom skill] Publish operator runbooks.** Cover health/readiness, queue backlogs, model/GitHub rate limits, timeouts, partial reviews, retries, alert response, audit lookup, incident escalation, data deletion, and recovery procedures.
- [ ] **D-05 (P0) [custom skill] Publish developer/reviewer guide.** Explain shadow and comment modes, finding severity/confidence, feedback and false-positive reporting, repository opt-out, review limitations, and the human review responsibilities.
- [ ] **D-06 (P1) [custom skill] Record pilot evaluation and expansion decision.** Summarize scope, quality/reliability metrics, known gaps, approved comment thresholds, incidents, owner sign-offs, and go/no-go criteria for broader rollout.
