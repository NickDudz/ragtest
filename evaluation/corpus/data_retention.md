# Meridian Information Retention Schedule

Document ID: MER-IG-501  
Owner: Information Governance  
Revision: 5.0  
Effective date: 2026-06-01

## Principles

This schedule defines how long Meridian Research Cooperative keeps common categories of information and what happens at the end of a retention period. It applies to authoritative records in applications, shared workspaces, managed devices, and approved paper files. A convenient duplicate does not gain a new retention period merely because it was copied to another location.

Retention begins at the trigger named for each record class, such as stand-down of an incident, completion of a shipment, termination of a contract, or retirement of an asset. The business owner identifies the record class, while Information Governance maintains the schedule and deletion controls. Legal decides the scope and release of legal holds.

The schedule uses minimum periods. Owners should not keep information longer without a documented business, legal, safety, or research need. Extra copies increase discovery effort, access risk, and the chance that an obsolete instruction will be mistaken for current guidance.

## Information classes

Public information is approved for unrestricted release. Internal information supports ordinary work and would cause limited harm if disclosed. Restricted information could create material harm, breach an obligation, expose personal data, reveal security controls, or compromise research or partner trust. The classification depends on content, not the file extension or storage system.

Working notes may be transitory when their substance is captured in an authoritative record. A draft that documents a material decision, approval, exception, or analysis may itself be a record. Employees do not use the transitory label to remove uncomfortable history or evade a hold.

## Core retention periods

Security incident case files are retained for three years after incident stand-down. Vehicle maintenance records are retained for the life of the vehicle plus five years. Sensor calibration records are retained for the life of the sensor plus three years. Visitor entry and exit records are retained for 18 months after the visit.

Cold-chain shipment records, including packing checks, custody transfers, temperature history, and disposition, are retained for two years after delivery or final disposal. Routine vehicle location telemetry is retained for 12 months. Fuel, charging, and vehicle assignment records are retained for two years after creation.

Executed contracts are retained for seven years after expiration or termination. Procurement bids not selected are retained for two years after award. General financial ledger records are retained for seven fiscal years. Ordinary internal meeting recordings are deleted after 30 days unless an approved transcript or decision record requires longer retention.

Restricted research datasets follow the approved research plan and participant or partner terms. If the plan specifies deletion after analysis, the owner records the analysis-complete date and removes direct identifiers at that trigger. De-identified derived data may have a separate approved retention period only when re-identification risk has been assessed.

## Legal holds

A legal hold suspends normal deletion for information within its stated scope, regardless of the ordinary retention date. Legal sends a written notice identifying custodians, systems, subjects, and date ranges as precisely as circumstances permit. Recipients acknowledge the notice and preserve relevant material without broadly copying unrelated information.

Only Legal may release a legal hold. When release is received, the records system does not delete everything immediately without review; it resumes the normal schedule and deletes material whose retention period has already expired during the next controlled cycle. Material subject to another hold remains preserved.

A hold applies to relevant information in active systems, managed exports, and scheduled deletion queues. Information Governance records the hold identifier in system metadata. Operational teams should not paste privileged legal advice into the record merely to show that a hold exists.

## Deletion and verification

Authoritative systems apply deletion monthly unless a record class requires a faster process. Deletion jobs produce counts, exceptions, and an execution identifier. Owners investigate failures such as missing classifications, unresolved holds, locked records, or unavailable storage. A job is complete only after exceptions are resolved or assigned.

Managed devices use approved secure deletion appropriate to the media and risk. Cryptographic erasure is acceptable when encryption keys are uniquely controlled and destruction is verifiable. Paper restricted records are cross-cut shredded through an approved service. Employees do not place restricted records in ordinary recycling.

Deletion verification samples the authoritative system, search index, and ordinary user-visible exports. It does not require altering immutable backups before their scheduled expiration. If data are later restored from a backup, the deletion ledger is reapplied before the system is released for use.

## Backups and replicas

Backups support recovery and follow the backup lifecycle rather than acting as ordinary record archives. Daily, monthly, and annual recovery copies may temporarily contain records removed from active systems. Access to those copies is limited, and restored data must be reconciled with deletion and hold ledgers.

A read replica, analytics warehouse, or search index is not automatically a backup. If users can query it during ordinary work, the owner must implement the record schedule there or rebuild it promptly from the corrected authoritative source. Derived tables document their source and refresh behavior so deletion can propagate.

Personal archives, offline mailbox files, and unmanaged exports are not approved ways to extend retention. A team needing a frozen analytical snapshot must define its purpose, owner, classification, access, expiration, and relationship to source deletion before creating it.

## Record ownership and transfers

Each application has a named business owner and technical custodian. The owner maps stored information to record classes and approves access; the custodian implements retention, holds, export, and deletion controls. Information Governance reviews mappings annually and when a system adds a materially different data type.

When work moves between teams, record ownership transfers in writing. The receiving owner confirms the classification, retention trigger, active holds, and authoritative location. The former team removes unnecessary duplicates after transfer verification rather than keeping a private safety copy indefinitely.

Departing workers transfer business records to the manager or designated system. Managers do not preserve an entire mailbox by default. They identify open obligations, decision records, contracts, and project material, then allow transitory and expired information to follow the schedule.

## Exceptions

An exception request identifies the record class, desired period, business reason, risk, compensating controls, and proposed end date. Information Governance and the relevant privacy, security, legal, or research owner review the request. An exception cannot override a legal minimum or permit deletion under an active hold.

Approved exceptions are reviewed at least annually. The system records the exception rather than silently changing the global schedule for all records. When the exception ends, ordinary deletion resumes and expired records enter the next controlled deletion cycle.

## Metrics and assurance

Information Governance reports coverage of classified systems, deletion success, unresolved exceptions, overdue ownership reviews, and hold acknowledgements. These measures indicate process health, not the value or performance of individual employees. A low deletion count may reflect a quiet month rather than compliance failure.

Internal audit selects representative systems and traces records from creation through classification, access, retention trigger, hold behavior, and deletion evidence. Findings distinguish a design gap from an isolated execution error. Corrective actions include an owner, due date, and evidence needed for closure.
