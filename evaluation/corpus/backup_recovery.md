# Meridian Backup and Recovery Runbook

Document ID: MER-OPS-204  
Owner: Platform Reliability  
Revision: 2.5  
Effective date: 2026-03-15

## Objectives

This runbook describes backup, restore, and continuity practices for Meridian Research Cooperative services. It covers production databases, application configuration, object storage, and the control records needed to rebuild a service. It does not replace a system-specific recovery plan. Each service owner maintains a short dependency map that names the identity provider, network path, secrets store, upstream feeds, and downstream consumers required for recovery.

Services are assigned to recovery tiers during architecture review. Tier 1 covers safety, shipment tracking, and identity services. Tier 2 covers business systems that can tolerate a longer interruption. Tier 3 covers archives, analysis sandboxes, and reproducible derived data. A tier determines objectives and testing frequency; it does not determine whether data deserves encryption or access control.

## Backup schedule and objectives

Tier 1 databases receive an encrypted full snapshot every 24 hours and transaction-log capture every 15 minutes, supporting a recovery point objective of 30 minutes. The Tier 1 recovery time objective is four hours from declaration of a recoverable outage. These targets are service objectives rather than guarantees. An incident report records any recovery that exceeds them and identifies whether the limiting factor was data transfer, dependency restoration, validation, or approval.

Tier 2 systems receive a full snapshot every 24 hours and have a recovery point objective of 24 hours and a recovery time objective of one business day. Tier 3 repositories receive a weekly snapshot when their source material cannot be reproduced. Derived Tier 3 datasets may be excluded if the owner documents the source inputs, build steps, and expected rebuild duration.

Configuration exports run after every approved production change and at least once daily. A snapshot without its matching schema, deployment manifest, encryption metadata, and restore instructions is considered incomplete. Backup jobs label artifacts with the service ID, environment, creation time in UTC, format version, and immutable content hash.

## Storage and isolation

The backup service writes first to an encrypted regional repository and then replicates completed artifacts to a second administrative domain. Production application credentials cannot delete the replicated copy. Backup operators use separate accounts with phishing-resistant multifactor authentication, and all deletion operations require a second operator's approval.

Backup payloads are encrypted in transit and at rest. Encryption keys are managed outside the backup repository, and the recovery envelope contains only a key reference, never the plaintext key. Key rotation must preserve the ability to restore retained snapshots. Before retiring an old key version, Platform Reliability performs a test restore of the oldest snapshot that depends on it.

The replicated repository is configured with object immutability for the first 35 days. After the immutable period, lifecycle rules apply the retention schedule. A legal hold can suspend lifecycle deletion, but a legal hold does not make an unreadable or corrupt backup acceptable. Integrity checks continue for held material.

## Retention

Daily snapshots are retained for 35 days, monthly snapshots for 13 months, and annual snapshots for seven years. Transaction logs expire with the daily recovery window unless a system-specific plan requires more. Retention is calculated from successful completion time, not job start time. Failed and partial artifacts are kept for seven days for troubleshooting and are never presented as recovery points.

Backup retention is not a substitute for the records schedule. When an authoritative record reaches its approved deletion date, the application removes it from active data and future backups. Existing immutable backups age out under the backup schedule and are protected from routine access. A restore performed after deletion must reapply the deletion ledger before the recovered service is released.

## Verification and restore drills

The backup service verifies hashes after upload and again after replication. A successful copy job is not counted as a verified backup until the destination hash matches and the catalog entry can be read. Daily monitoring alerts on missed schedules, unexpected size changes, replication lag, and catalog errors. Operators investigate changes against deployments and normal data growth before declaring corruption.

Platform Reliability performs a Tier 1 restore drill every quarter and a Tier 2 restore drill twice per year. Each drill restores into an isolated environment, uses the documented recovery envelope, and validates application-level behavior rather than merely opening a backup file. Tier 3 owners test a representative restore annually.

A drill record captures the selected recovery point, artifact hashes, start and finish times, personnel, dependencies, validation queries, observed data loss, and corrective actions. The selected snapshot should rotate so the team exercises recent, monthly, and key-rotation boundaries over time. A failed drill opens a corrective work item with an owner and target date; it does not automatically trigger a production incident.

## Declaring and performing a recovery

The incident commander declares a recovery after consulting the service owner and Platform Reliability lead. The declaration identifies the affected service, suspected failure time, latest trustworthy recovery point, and business priority. Operators preserve evidence from the failed environment before destructive repair when doing so will not worsen a safety impact.

Recovery begins in an isolated network segment. Operators restore identity and secrets references, load the selected snapshot, replay eligible transaction logs, and run the service-specific validation checklist. Validation covers record counts, known sentinel records, authorization behavior, recent business transactions, external interfaces, and monitoring. The service owner accepts the restored state before traffic is shifted.

If validation fails, operators do not repeatedly overwrite the same recovery environment. They record the failure, preserve logs, and create a clean attempt from the next suitable recovery point. This separation prevents a repair action from being mistaken for corruption in the original artifact.

## Return to service

Traffic returns gradually when the platform supports staged release. Monitoring is temporarily tightened for error rate, queue depth, authentication failures, and data reconciliation differences. The team announces the recovery point actually used and any confirmed data-loss interval. Customer or partner communication follows the incident communication plan rather than an improvised technical update.

Within two business days, the service owner reconciles transactions created near the outage boundary. The incident record links the backup catalog entries and drill history relevant to the event. Corrective work may change the tier, schedule, architecture, or validation suite, but changes follow ordinary review after immediate service has stabilized.

## Local and disconnected sites

Field sites may keep an encrypted local export when network capacity prevents timely central backup. The site lead records the export hash and transfers it to the regional repository within 48 hours of connectivity returning. Local exports use managed media, remain physically controlled, and are erased after central verification. Consumer removable drives are not approved backup media.

An offline export is not considered a successful central backup and does not pause missed-backup alerts. The service owner documents the exposure when an outage exceeds the recovery point objective. Once connectivity returns, newer transaction logs are uploaded before operators remove the local recovery copy.
