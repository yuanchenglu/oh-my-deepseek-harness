# Security Policy

## Project status and supported versions

`oh-my-deepseek-harness` is currently an **Experimental Preview**. No Public Beta or Stable release is considered security-supported until its Release Gate and artifact verification are complete.

| Line | Security support |
|---|---|
| `develop` | Receives current security fixes and validation work |
| `v3.0.0-beta.N` | Latest published Beta only, after a Beta actually exists |
| `v3.0.0` | Latest published Stable line, after Stable actually exists |
| Older prereleases, source snapshots, forks and unsupported environments | Best effort only |

A version string, green unit test run, branch merge or Git tag does not by itself establish a supported release.

## Report a vulnerability privately

**Do not disclose vulnerability details in a public Issue, Pull Request, Discussion, commit message, test artifact or log.** Do not include exploit code, API keys, private data, unredacted prompts, user files or credentials in public channels.

Use GitHub's private vulnerability reporting channel:

[Report a vulnerability privately](https://github.com/yuanchenglu/oh-my-deepseek-harness/security/advisories/new)

If the private-reporting entry is unavailable, do not publish the details. Open a minimal public Issue stating only that the private security channel is unavailable, with no vulnerability description, exploit evidence, affected paths or sensitive logs. The maintainer will establish a private channel before requesting details.

Before any Public Beta or Stable release, the release coordinator must verify that GitHub Private Vulnerability Reporting is enabled and usable from a non-maintainer account.

## What to include

Provide the minimum information needed to reproduce and assess the issue:

- affected version, commit SHA or artifact hash;
- OS, Python version and Hermes version/source;
- attack prerequisites and trust boundary;
- exact redacted reproduction steps;
- expected and observed behavior;
- security impact and data affected;
- whether exploitation is active or publicly known;
- suggested mitigation, if available;
- a safe way to contact the reporter through the advisory thread.

Replace secrets and personal data with deterministic placeholders. Attach only the smallest required artifact. Never submit a real user database, full conversation history, `.env`, provider token or unredacted Tool output.

## In-scope security areas

Reports are in scope when they affect the repository's supported or target behavior, including:

- unintended external transmission of prompts, Tool arguments, Memory or secrets;
- redaction, consent or logging failures;
- path traversal, symlink escape or unsafe purge/uninstall behavior;
- local API exposure beyond the documented loopback boundary;
- command injection, SQL injection or unsafe subprocess construction;
- unsafe install, upgrade, migration, rollback or backup behavior;
- privilege or permission errors in product files and runtime state;
- dependency, build, release, provenance or package-supply-chain compromise;
- prompt injection that bypasses structural authorization or destructive-operation confirmation;
- cross-session data leakage or security-relevant data-integrity failures.

The Beta does not promise a secure remote multi-user service. A report about intentionally binding an independently modified fork to a public interface may be out of scope, but a default or documented path that unexpectedly exposes the local service remains in scope.

## Generally out of scope

The following normally do not qualify unless they create a concrete security impact:

- unsupported operating systems, Python versions or Hermes versions;
- social engineering without a product or repository weakness;
- denial of service requiring control of the same local user account and no privilege boundary crossing;
- missing hardening that is already documented as an unsupported remote-deployment scenario;
- automated scanner output without a reproducible vulnerable path;
- vulnerabilities only in an unmodified upstream dependency when this project does not expose or worsen the affected path;
- public claims without artifact, commit or reproducible evidence.

## Severity and release impact

| Severity | Project interpretation | Release effect |
|---|---|---|
| P0 / Critical | active exploitation, credential or private-data disclosure, arbitrary code execution across a trust boundary, destructive data loss, release-signing compromise, or rollback failure leaving users unsafe | Stop promotion and release work; block the next Gate until contained and verified |
| P1 / High | serious security or integrity failure with realistic prerequisites and no safe default mitigation | Must be fixed or receive an explicit time-bounded waiver allowed by the release plan; Stable cannot carry an open P1 |
| P2 / Medium | limited impact, stronger prerequisites or effective documented mitigation | Track with owner, test and target milestone |
| P3 / Low | defense-in-depth or low-impact hardening | Track when actionable; does not override higher-priority release work |

Final severity is assigned during triage and may change as evidence develops.

## Response targets

These are maintenance targets, not contractual service-level guarantees:

- acknowledge a complete private report within **3 business days**;
- provide initial severity and scope assessment within **7 business days**;
- provide an update at least every **7 business days** while active investigation continues;
- for a credible P0, begin containment immediately and pause affected promotion/release work;
- coordinate remediation, regression tests, advisory text and disclosure timing with the reporter.

Complex reports, upstream coordination and maintainer availability may change the schedule. The advisory thread is the source of truth for status.

## Coordinated disclosure

Please keep the report private until the maintainer confirms that affected supported artifacts are fixed or mitigated and disclosure material is ready. The project will not move or overwrite an existing tag or artifact to conceal a vulnerability. A corrected prerelease receives a new version and immutable artifacts.

When disclosure is appropriate, the project may publish:

- a GitHub Security Advisory;
- affected and fixed versions or commit ranges;
- severity and impact summary;
- migration, mitigation and rollback instructions;
- regression-test and artifact evidence;
- reporter credit, if requested and legally permissible.

## Safe-harbor intent

Good-faith research is welcome when it:

- avoids privacy violations, data destruction and service disruption;
- uses accounts, devices and data the researcher owns or is authorized to test;
- stops after demonstrating the minimum necessary impact;
- reports privately and allows reasonable remediation time;
- does not extort, threaten or demand payment as a condition of non-disclosure.

The project cannot authorize testing against third-party systems, DeepSeek, Hermes, package registries or other infrastructure it does not own.

## Maintainer handling requirements

Maintainers must:

- keep reports in the private advisory thread;
- avoid copying secrets or private evidence into public Issues/PRs;
- create a redacted Work ID and regression test when code changes are required;
- record severity, owner, affected versions, mitigation and disclosure decision;
- rerun every affected Gate after remediation;
- increment the prerelease version when a published Beta requires replacement;
- retain only the minimum sensitive material needed for coordination.

See [`docs/release/RELEASE_CHECKLIST.md`](docs/release/RELEASE_CHECKLIST.md) for the release security gate.