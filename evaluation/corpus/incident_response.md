# Meridian Incident Response Procedure

Document ID: MER-SEC-310  
Owner: Incident Management  
Revision: 4.1  
Effective date: 2026-05-10

## Purpose

This procedure gives Meridian Research Cooperative a common method for detecting, declaring, containing, and learning from operational and security incidents. It applies to technology failures, data exposure, facility access anomalies, shipment-control failures, and safety-relevant service disruptions. Specialized teams may add checklists, but they use the same severity language, command roles, evidence discipline, and closure process.

An alert is an observation that needs triage. An event is a confirmed occurrence that may be routine. An incident is an event requiring coordinated response to limit harm or restore service. Treating every alert as a declared incident creates noise, while delaying declaration to protect a metric creates unmanaged risk. The duty manager may declare with incomplete information and revise severity as evidence improves.

## Detection and intake

The response desk accepts automated alerts, employee reports, partner notifications, and observations from field teams. The first responder opens an incident record, notes the reporter and time, preserves the original message, and identifies affected services, locations, devices, or data when known. Reports involving personal safety are routed to emergency services before technical diagnosis.

Employees report suspected loss of restricted data, stolen managed devices, unauthorized access, or intentional control bypass immediately. A reporter is not expected to prove compromise. The response desk acknowledges a high-risk report within 15 minutes and assigns an initial triage owner. Ordinary reliability alerts are acknowledged according to the service's on-call target.

## Severity

A Severity 1 incident involves an active threat to life, confirmed widespread exposure of restricted data, or complete loss of a Tier 1 service with no viable workaround. Severity 1 also applies when several lower-impact failures combine into an immediate safety risk. The duty manager pages executive, legal, safety, and communications contacts according to the call tree.

Severity 2 covers material but contained impact, including a Tier 1 service operating through a degraded workaround, confirmed restricted-data exposure limited to a small known set, or a site outage that blocks time-sensitive work. Severity 3 covers localized interruption, suspicious activity under investigation, or a missed control with no current evidence of harm. Severity 4 is used for minor operational defects that still benefit from a tracked response.

Severity is based on current impact and credible near-term risk, not the seniority of the reporter or the number of messages in a channel. The incident commander reviews severity after containment, after each material discovery, and before standing down. A downgrade never deletes the record of the highest severity reached.

## Command roles

The incident commander sets objectives, assigns response roles, approves major containment actions, and maintains the next update time. The commander coordinates decisions but should not personally perform every diagnostic task. For Severity 1 and Severity 2 events, a separate scribe maintains the timeline and a technical lead directs investigation. A communications lead prepares internal and external updates, while a safety or privacy specialist joins when the impact requires that expertise.

Every role has one named owner at a time. A handoff states current impact, completed actions, open hypotheses, risky changes, next decision, and next update deadline. The outgoing owner remains available until the incoming owner repeats back the essential state or records an explicit acceptance in the incident channel.

The commander may authorize an emergency change when waiting for the ordinary approval path would materially increase harm. The scribe records the reason, expected effect, rollback condition, and approving commander before the action when possible. Emergency status does not excuse an undocumented permanent change after the incident stabilizes.

## Containment and investigation

Responders choose containment proportionate to harm. They may revoke a device credential, isolate a host, suspend a shipment, disable a badge, block a network path, or move traffic to a verified recovery environment. Broad shutdowns can destroy evidence and increase service impact, so the technical lead states the expected benefit and likely collateral effect before approval.

Hypotheses are labeled as untested, supported, or disproved. The timeline distinguishes observed facts from interpretation. Responders preserve volatile evidence first when it is relevant and safe, then collect durable logs, configuration state, hashes, photographs, access records, or sensor histories. Original evidence remains unchanged; analysis uses a working copy whenever practical.

Incident evidence is stored in the restricted case workspace with a recorded collector, collection time, source, and SHA-256 hash. The scribe links each evidence item to the timeline entry or hypothesis it supports. Access to the case workspace is limited to response roles and later reviewers with a documented need.

## Communication

For Severity 1, internal updates occur at least every 30 minutes until the commander sets a different justified interval. Severity 2 updates occur at least hourly during active response. Each update states confirmed impact, current containment, what changed since the last update, the next action, and the next update time. Updates avoid unsupported attribution and do not speculate about an individual person's intent.

External statements are approved by the communications lead and the relevant legal, privacy, safety, or customer owner. Technical responders provide verified facts and uncertainty ranges but do not contact affected customers independently unless assigned. If the team cannot yet answer a material question, the update says what is being checked and when another update is expected.

## Recovery and validation

Containment stops or limits harm; recovery restores an acceptable service or process. The service owner defines validation criteria before return to normal operation. Criteria may include known-good transactions, authorization checks, sensor comparisons, queue reconciliation, partner confirmation, or controlled shipment inspection. Monitoring remains elevated through an agreed observation window.

A workaround may support recovery without closing the incident. The commander records residual risk, workaround owner, expiration condition, and planned permanent correction. If recovered data comes from a backup, the incident record identifies the chosen recovery point and confirmed loss interval rather than describing recovery as complete without qualification.

## Closure and review

The commander stands down active response when immediate harm is controlled, the service owner accepts validation, and every residual risk has an owner. The scribe completes the timeline, links evidence, records the highest severity, and lists follow-up work. Closing an incident does not erase alerts or merge inconvenient gaps in the timeline.

For Severity 1 and Severity 2 incidents, the owner publishes a blameless post-incident review within five business days of stand-down. The review describes impact, detection, contributing conditions, response decisions, recovery, what worked, and corrective actions. Severity 3 incidents receive a review when the commander finds a reusable lesson or repeated control failure.

Corrective actions have a named owner, measurable completion condition, and due date. The Incident Management lead reviews overdue actions monthly. An action is closed only with evidence of the changed control, test, documentation, or accepted risk decision; a statement that work began is not completion evidence.

## Record retention and legal hold

Incident records, timelines, evidence inventories, and final reviews are normally retained for three years after stand-down. Evidence containing restricted data remains access-controlled throughout that period. A legal hold notice overrides scheduled deletion for the identified incident material until Legal releases the hold in writing. The case owner records the hold identifier without copying legal advice into ordinary operational channels.

When the retention period ends without a hold, the case workspace is deleted through the approved records process. Aggregate lessons and non-identifying metrics may remain in the reliability knowledge base. Those summaries must not contain credentials, personal data, customer secrets, or evidence copied merely for convenience.

## Exercises

Incident Management runs two cross-functional exercises each year. At least one exercise includes an unavailable dependency or misleading alert so responders practice uncertainty rather than a scripted happy path. Exercise records are marked as simulations, stored separately from real cases, and used to update call trees, role cards, and validation checklists.
