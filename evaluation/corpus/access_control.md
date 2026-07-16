# Meridian Access and Visitor Control Standard

Document ID: MER-SEC-101  
Owner: Security Operations  
Revision: 3.2  
Effective date: 2026-04-01

## Purpose and scope

This standard defines physical and logical access controls for Meridian Research Cooperative offices, laboratories, storage rooms, and temporary field sites. It applies to employees, contractors, visitors, service vendors, and any device credential issued by Meridian. Access is granted for a business purpose, limited to the smallest useful scope, and reviewed on a predictable schedule. A badge, key, token, or temporary code never establishes permission by itself; it only represents a permission recorded in the access register.

The Security Operations desk owns the access register. Site leads approve ordinary access for their locations, while system owners approve access to restricted applications. A person may have different expiration dates for a building badge, a laboratory endorsement, and a virtual private network credential. Shared credentials are prohibited because they prevent reliable attribution during an incident review.

## Identity proofing and issue

Human Resources sends the Security Operations desk an approved identity record before a permanent badge is issued. The desk compares one government-issued photo document with the approved record and records the verification result, but it does not retain a scan of the identity document. Contractors must also have a named Meridian sponsor and an end date. Contractor access expires at 18:00 local time on that end date unless the sponsor submits an approved extension.

New badges are handed directly to the named person after the person acknowledges the acceptable-use statement. Badges must not be mailed through ordinary internal mail, left at reception for unattended pickup, or transferred between workers. Laboratory endorsements are encoded separately from general door access so that a building-wide change does not silently broaden laboratory privileges.

## Least privilege and reviews

Site leads review active building access every quarter. Application owners review privileged logical access every month and ordinary logical access every quarter. The access register produces an exception list containing inactive sponsors, expired training, missing end dates, and accounts unused for 90 days. Reviewers must resolve each exception as retained with justification, reduced, suspended, or revoked.

Temporary field-site access is tied to the deployment record rather than copied from a worker's home office profile. A field lead may approve access through the planned demobilization date, but not longer than 120 days in one approval. Requests beyond 120 days require a new review of site need, safety training, and sponsor status.

## Lost, stolen, and damaged credentials

A lost or stolen badge must be reported to the Security Operations desk immediately; the desk disables it within 15 minutes of receiving the report. The worker also informs the site lead when the badge could identify a restricted location or was lost with a Meridian device. A replacement receives a new credential number. The old number is never reactivated, even if the original badge is later found.

A damaged badge that remains in the worker's possession may be exchanged at the desk. The desk disables the damaged credential before activating its replacement. Repeated damage is handled as an equipment issue, not automatically as misconduct, but Security Operations may examine the badge for evidence of tampering.

For a lost hardware token or managed field tablet, the service desk revokes the associated device credential and remote session tokens within 30 minutes of the report. If the item stored restricted data, the reporter must also open a security incident and identify the last known location, approximate loss time, and whether full-disk encryption was active.

## Visitors and vendors

Every visitor must have a named sponsor, a visit purpose, and an expected departure time. Reception verifies the visitor's name, issues a visibly different temporary badge, and records entry and exit. Visitors remain escorted in laboratories, network rooms, archive rooms, and loading areas marked as restricted. A sponsor may transfer escort responsibility to another authorized employee by notifying reception before the transfer.

Visitor badges expire at midnight on the issue date and are collected at exit. Multi-day vendors receive a new badge each day; a purchase order or work ticket is not a standing access credential. Reception reconciles unreturned badges at close of business and alerts Security Operations when the visitor cannot be contacted.

Visitor entry and exit records are retained for 18 months, then deleted during the next monthly records cycle unless a legal hold applies. The record contains the visitor name, sponsor, purpose, issued badge number, entry time, and exit time. Reception notes may describe an access exception, but must not include medical information, payment-card data, or a copy of an identity document.

## Emergency access

During a threat to life or facility safety, the incident commander may authorize an emergency door override for a defined zone. An emergency door override expires after 15 minutes and requires a Security Operations review by the end of the next business day. The authorization record must identify the commander, affected doors, reason, start time, and termination time. Emergency access is not used to avoid an ordinary approval delay or to support routine maintenance.

If the access-control server is unavailable, guards use the printed emergency roster stored in the sealed response cabinet. Two guards must record each manual entry to a restricted zone. When service returns, Security Operations reconciles those entries with the electronic register and reports any unmatched event as an access anomaly.

## Departures and role changes

Human Resources notifies Security Operations of an involuntary departure before the scheduled meeting. Security Operations disables logical access at the instructed time and collects physical credentials with the manager. For an ordinary departure, access ends no later than the worker's recorded final hour. A manager may not keep an account active for convenience after the worker leaves.

Role changes trigger a fresh least-privilege review. Old permissions are removed before or at the same time as new permissions are activated. Temporary overlap is allowed for up to five business days only when both managers approve a documented transition task. Privileged roles may not overlap unless the Security Operations manager approves the exception.

## Monitoring and exceptions

Door controllers send access events to the security log service. Repeated denials, access outside an approved schedule, and use of a disabled badge generate alerts. Alerts are triaged according to the incident response procedure; an alert does not by itself prove misuse. Routine access logs are not used to measure employee productivity.

Exceptions require a written business reason, compensating control, owner, and expiration date. Security Operations may approve an exception for at most 90 days. Renewal requires evidence that the compensating control worked and that a permanent correction remains impractical. The register links an exception to the affected credential so reviewers can see the complete access decision.
