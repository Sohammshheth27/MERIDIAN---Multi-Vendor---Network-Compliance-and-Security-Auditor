# MERIDIAN

**Network Compliance and Security Auditor**

MERIDIAN is a vendor-agnostic configuration assurance platform for network and
security infrastructure. It ingests a device configuration — uploaded, or
collected over SSH — normalises it into a common security model, evaluates it
against a catalogue of security controls, and produces an assessment in which
every assertion is traceable to the exact file and line that produced it.

---

## Table of contents

- [The console](#the-console)
- [Design principles](#design-principles)
- [Capabilities](#capabilities)
- [Compliance framework coverage](#compliance-framework-coverage)
- [Architecture](#architecture)
- [Installation](#installation)
- [Operation](#operation)
- [Extending platform support](#extending-platform-support)
- [Application security posture](#application-security-posture)
- [Data handling and licensing](#data-handling-and-licensing)
- [Validation status](#validation-status)

---

## The console

### Overview

The landing view reports the state of the estate: assessments in progress,
mappings learned through the training interface, and the average compliance
score across audited devices.

![Dashboard](docs/screenshots/01-dashboard.png)

### Assessment register

Every assessment is retained and addressable, with vendor, platform,
compliance score and status. Results may be exported as CSV, and a previously
issued report may be re-verified against its signature.

![Assessments](docs/screenshots/02-assessments.png)

### Assessment overview

Framework scores are reported per framework, each with the number of
requirements met and the number that remain undecided. Configuration coverage
is displayed alongside the score rather than behind it, and a framework that
publishes no requirements for the platform states that instead of reporting
zero.

![Assessment overview](docs/screenshots/03-assessment-overview.png)

### Findings

Findings are aligned to a chosen framework, and carry severity, the control
that produced them, the framework requirements they cite, and a result state.
`PASS`, `FAIL` and `UNKNOWN` are distinct outcomes and are rendered as such:
an undecided control is never presented as a pass.

![Findings](docs/screenshots/04-findings.png)

### Interface inventory

The addressing from which multi-device topology is inferred. Adjacency is
derived from shared subnets rather than read from the wire, and the view says
so, because an inference presented as an observation is a claim the platform
has not earned.

![Interfaces](docs/screenshots/05-interfaces.png)

### Topology

Zones are arranged by trust tier, with the enforcement point drawn between
them. Every `any`/`any` flow into a more trusted zone is drawn and labelled
with the rule that permits it. A flow whose zone currently contains no
interface is marked `latent`: permitted by policy, but not presently
traversable.

![Topology](docs/screenshots/06-topology.png)

### Known vulnerabilities

Published vulnerabilities affecting the exact firmware and hardware model the
device reports. Both version and model must match before a vulnerability is
listed. The view states the date of the vulnerability data it used, and
distinguishes a device that is affected from a configuration check that
failed — the remedy for the former is a firmware update, not a setting.

![Known vulnerabilities](docs/screenshots/07-known-vulnerabilities.png)

### Training

Settings the mapping packs do not recognise are queued for operator review,
ranked by a calibrated confidence score. The measured precision at each
confidence band is displayed, so the operator knows what the ranking is worth
and does not mistake a high score for a decision already made.

![Training](docs/screenshots/08-training-loop.png)

---

## Design principles

### Absence is never reported as a positive result

The governing rule of the platform is that a control which could not be
evaluated is never recorded as compliant. Where a configuration is silent, the
assessment states that it is silent. This principle determines the result
model, the scoring method, and the conditions under which a control may be
excluded from scoring.

Most tools in this category report two states. MERIDIAN reports seven.

| State | Definition |
|---|---|
| `PASS` | The control was evaluated and the device satisfies it. |
| `FAIL` | The control was evaluated and the device does not satisfy it. |
| `PARTIAL` | The control is scoped to multiple instances; some comply and others do not. |
| `NOT_APPLICABLE` | The control does not apply to this platform or deployment, and the justification is recorded. |
| `UNKNOWN` | The control could not be evaluated. This is neither a pass nor a failure. |
| `MANUAL_REVIEW` | The control requires human judgement; no automated verdict would be defensible. |
| `ERROR` | The evaluation itself failed. This is a defect in the platform, not in the device. |

### Scoring is reported with its coverage

`score_pct` is calculated across decided controls only, and is never published
without `assessed_pct` alongside it. A device for which 40 percent of the
relevant settings could be read, all of which passed, is reported as scoring
100 percent at 40 percent coverage. It is never reported as scoring 100
percent.

### Exclusion from scoring is the platform's strictest invariant

`UNKNOWN` remains in the denominator and therefore depresses coverage.
`NOT_APPLICABLE` is excluded from scoring entirely, which means an incorrect
exclusion silently raises the score by removing a control from the
denominator. Over-application of `NOT_APPLICABLE` is consequently the most
direct way in which a tool of this kind can misrepresent a device.

Every `NOT_APPLICABLE` verdict must therefore satisfy one of three conditions,
each of which is recorded as evidence:

1. **The platform is incapable of the control.** Declared per field or per
   domain, with a written justification.
2. **The relevant feature is not in use.** Gated on an observed setting, which
   is cited as the evidence for the exclusion.
3. **Neither condition holds.** The control is then recorded as `UNKNOWN` and
   remains in the denominator.

Every `NOT_APPLICABLE` verdict produced across the bundled configurations
carries a justification. A test enumerates all of them and fails on the first
that cannot supply one.

---

## Capabilities

### Configuration ingestion and normalisation

| Capability | Description |
|---|---|
| Multi-vendor parsing | Thirteen mapping packs spanning ten platforms and six grammar families. Vendor support is expressed as data, not code. |
| Live collection | Read-only `show` commands over SSH. Credentials are used for the session and are not persisted. |
| Record accounting | Every source record is classified as parsed, unreadable, mapped, or parsed-but-unmapped, so parsing coverage is itself measurable. |
| Redaction | Addresses and secrets are pseudonymised on ingest. Pseudonymisation preserves network prefixes, so subnet relationships survive redaction and topology remains analysable. |
| Parser cross-check | Two independent parsing methods are run over the same device and their results reconciled, so a single parser defect does not silently become a finding. |

### Compliance evaluation

| Capability | Description |
|---|---|
| Control catalogue | Eighty-eight controls, each evaluated against the normalised model and each citing the evidence behind its verdict. |
| Framework mapping | Findings are mapped to external framework requirements with the provenance chain recorded. |
| Strictness profiles | Framework-specific evaluation profiles, so a control may be assessed against the standard being applied rather than a single fixed threshold. |
| Manual review routing | Controls that cannot be decided mechanically are routed for human decision rather than guessed. |

### Policy and rule analysis

| Capability | Description |
|---|---|
| Rule hygiene | Detection of dead, shadowed, redundant and over-broad policy entries. |
| Reachability analysis | Determines whether specified traffic would be permitted, and identifies the rule that decides the outcome. |
| Blast radius | From a compromised zone, enumerates every zone reachable over lateral-movement ports together with the permitting rule. Paths are marked `LATENT` where no host currently occupies the zone. |
| Recertification | Identifies rules due for review. Deletion is recommended only where three independent signals agree. |
| Log correlation | Distinguishes a genuinely unused rule from one whose counters were reset. |

### Remediation

| Capability | Description |
|---|---|
| Remediation guidance | Vendor-correct commands for each finding, checked against lockout conditions before being proposed. |
| Hardened configuration generation | Generates a complete hardened configuration for the target vendor, anchored on observed evidence and preserving the device's own value formats. Type mismatches are refused rather than coerced. |
| What-if analysis | Re-scores a copy of the device with proposed fixes applied or rules disabled, and warns where an IPv6 counterpart would still permit the traffic. |

### Infrastructure and threat context

| Capability | Description |
|---|---|
| Multi-device topology | A fabric assembled from several assessed devices, with trust tiers rendered. |
| Change tracking | Snapshot and differential comparison, distinguishing a change in the device from a change in the analysis. |
| Known vulnerabilities | Firmware evaluated against a dated NVD snapshot and the CISA KEV catalogue. Both version and hardware model must match before a vulnerability is reported. |
| Adversary technique mapping | Each control is associated with the MITRE ATT&CK technique it mitigates. |
| VPN assessment | Per-tunnel perfect forward secrecy, anti-replay, security association lifetimes, and management exposure over the tunnel. |
| Wireless assessment | Open, WEP and TKIP detection, protected management frames, guest isolation, and cleartext pre-shared keys. |
| Host firewall | Windows and iptables configurations assessed through the same analysers used for appliances. |
| Cloud firewalls | AWS security groups, Azure network security groups, and GCP VPC firewall rules. |

### Reporting and assurance

| Capability | Description |
|---|---|
| Tamper-evident reports | Reports carry a content hash and signature, so alteration after issue is detectable. |
| Scheduled re-collection | Periodic re-assessment with alerting on configuration drift. |
| Fleet view | Cross-device reporting with CSV export. |
| Learning loop | Unmapped settings are queued for operator review and ranked by a calibrated confidence score. |

### Extended checks are reported beside the score, not inside it

VPN, wireless and vulnerability findings are presented alongside the
compliance score and do not alter it. Incorporating them into the
eighty-eight-control catalogue would have changed the score and coverage of
every device previously assessed, including results already issued. These
checks follow the same evidentiary rules as the control catalogue: each
failure cites the setting responsible, and any value that cannot be decoded is
reported as undecided rather than inferred.

---

## Compliance framework coverage

**5,785 requirements** across the following frameworks:

| Framework | Scope |
|---|---|
| NIST SP 800-53 | Security and privacy controls |
| DISA STIG | Defense Information Systems Agency hardening guidance |
| CIS Benchmarks | Referenced by identifier and short title |
| ISO/IEC 27001 | Referenced by clause number and short title |
| NIST SP 800-171 r3 | Controlled unclassified information |
| PCI DSS 4.0 | Payment card industry data security |
| CMMC | Cybersecurity maturity model certification |
| NERC CIP | Critical infrastructure protection |

Provenance is chained: STIG to CCI to NIST SP 800-53 to ISO/IEC 27001 and
NIST SP 800-171.

---

## Architecture

| Layer | Technology | Responsibility |
|---|---|---|
| Engine | Python, FastAPI | Parsing, normalisation, evaluation, reporting |
| Console | React, TypeScript, Vite | Operator interface |
| Mapping packs | YAML | Vendor and platform support, expressed as data |
| Control catalogue | YAML | Security control definitions and framework citations |

The console is built into the engine package, so a deployment serves both the
application programming interface and the operator interface from a single
process and a single origin.

---

## Installation

Requirements: Python 3.11 or later, and Node.js 20 or later to build the
console.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux, macOS

pip install -r requirements.txt

cd frontend && npm install && npm run build && cd ..
```

## Operation

```bash
python -m uvicorn meridian.api.app:app --host 127.0.0.1 --port 8000
```

The console is then available at `http://127.0.0.1:8000/dashboard`, and the
application programming interface documentation at `http://127.0.0.1:8000/docs`.

For console development with hot reloading, run the engine as above and start
the development server separately. It proxies the application programming
interface to the engine, so a single origin is presented to the browser.

```bash
cd frontend && npm run dev
```

### Configuration

| Variable | Purpose |
|---|---|
| `MERIDIAN_ADMIN_USER` | Console account name. |
| `MERIDIAN_ADMIN_PASSWORD_HASH` | bcrypt hash of the console password. |
| `MERIDIAN_CONSOLE_AUTH` | Set to `0` to disable console authentication for local development. |
| `MERIDIAN_API_TOKEN` | Bearer token required for programmatic access. |
| `MERIDIAN_DATA_DIR` | Location of uploaded configurations and the assessment store. |
| `MERIDIAN_PACKS_DIR` | Location of mapping packs. |
| `MERIDIAN_CORS_ORIGINS` | Permitted cross-origin callers. |
| `MERIDIAN_MONITOR` | Set to `1` to enable scheduled re-collection. |
| `MERIDIAN_SHOW_PAIRING` | Set to `1` to keep the authenticator pairing code available after enrolment. Intended for demonstration only. |

### Threat data

Vulnerability lookup and adversary technique mapping operate from local data
files, so results are reproducible and each states the date of the data it
used. A vulnerability result derived from data more than thirty days old
declares that fact before its findings.

```bash
python -m tools.fetch_cve
```

---

## Extending platform support

A new platform is a YAML file rather than a code change.

```yaml
vendor: acme
platform: acme_os
reader: indented
mappings:
  - field: management.ssh.enabled
    regex: '^ip ssh server$'
    value: {const: true}
not_applicable_fields:
  authentication.enable_secret: "AcmeOS has no enable-secret concept"
```

A pack validated only against a fixture written alongside it is assigned
version `0.9`. A test prevents it from being promoted to `1.0` until it has
been validated against output from a real device. This distinction is
maintained because real configurations expose defects that constructed
fixtures do not: a downloaded PAN-OS export identified a defect in the XML
reader within minutes of first use.

---

## Application security posture

The platform is built to satisfy the controls it assesses.

| Measure | Corresponding control |
|---|---|
| Console credentials stored as a bcrypt hash; no plaintext credential in the repository or its history | `MERIDIAN-PLT-002` |
| Account lockout after repeated authentication failures | `MERIDIAN-EXT-013` |
| Multi-factor authentication for administrative access, by time-based one-time password | `MERIDIAN-EXT-014` |
| Authentication failures recorded | `MERIDIAN-EXT-021` |

One-time codes conform to RFC 6238 and are compatible with standard
authenticator applications. One-time codes are accepted once; replay of a
previously accepted code is refused. Sessions are held in session storage and
expire with the browser session.

The pairing endpoint, which discloses the shared secret, closes after the
first successful authentication. It may be held open for demonstration by
setting `MERIDIAN_SHOW_PAIRING=1`, in which case the engine records a warning
at startup stating that the control has been relaxed.

---

## Data handling and licensing

The following are deliberately excluded from this repository.

| Excluded | Reason |
|---|---|
| CIS Benchmark and ISO/IEC 27001 text | Copyrighted. Referenced by identifier and short title only. Licence handling is enforced in the type system rather than by policy. |
| Vendor documentation | Retaining a local copy against which to write mappings is fair use; republishing a vendor's command reference is not. Sources are recorded so that each may be retrieved independently. |
| Real device configurations and assessment history | The change-tracking store keys on hostname, serial number and configuration digest. Publishing it would disclose live infrastructure. |
| NIST OSCAL catalogues | Public domain, but retrievable on demand and large enough to dominate the repository. |

These exclusions are enforced by `.gitignore` and, for licensed content, in
code.

---

## Validation status

Mapping packs for SonicWall, PAN-OS, Cisco IOS-XE, Cisco ASA and Juniper are
validated against real or captured device configurations. Packs for Arista,
Aruba, FortiOS, Azure and GCP are at version `0.9`, validated against
constructed fixtures pending real exports.

Among the extended checks, the VPN, vulnerability and wireless assessments are
validated against a real SonicWall NSA 3700 export comprising 92,635 settings.
The Catalyst 9800 wireless adapter is validated against a fixture constructed
from the vendor's published command reference, and every result it produces
declares that basis.

```bash
python -m pytest -q
```
