# Meridian Remote Site Connectivity Handbook

Document ID: MER-NET-240  
Owner: Network Reliability  
Revision: 3.4  
Effective date: 2026-04-18

## Purpose and design

This handbook defines connectivity for Meridian Research Cooperative field stations, temporary laboratories, and monitoring shelters. Remote networks must support safe local operation when a wide-area link is degraded or absent. A central dashboard is useful, but a site must not depend on an uninterrupted dashboard session to recognize a local temperature alarm, stop unsafe equipment, or record a custody transfer.

Each site has a network profile naming its business owner, technical custodian, primary and backup links, address ranges, expected traffic, local services, monitoring contacts, and demobilization date when temporary. Field teams use approved managed routers; personal hotspots may support emergency communication but are not bridged into a restricted site network.

## Network zones

Sites separate managed user devices, sensors and controllers, guest access, and administrative interfaces. Firewall rules allow only documented flows between zones. A sensor that needs to publish readings to a local gateway does not receive broad access to employee laptops or router administration. Guest traffic reaches the internet directly and cannot route to Meridian address space.

Administrative access uses the management tunnel and phishing-resistant multifactor authentication. Router management is not exposed directly to the public internet. Emergency local administration requires a sealed site credential, two-person access, and a record of commands that is uploaded when connectivity returns.

## Primary and backup links

The preferred primary link is wired broadband or managed fixed wireless when available. A cellular link provides backup at permanent sites with time-sensitive operations. Satellite may be selected where terrain or carrier coverage makes cellular unreliable. Link choice considers latency, data caps, antenna placement, weather exposure, power draw, repair lead time, and whether a provider shares physical infrastructure with the primary path.

The managed router tests reachability through each link every 10 seconds. It fails over after six consecutive failed probes, which represents approximately 60 seconds of sustained loss. A single missed probe does not change paths. The router returns to the primary link only after five minutes of stable probes to avoid oscillation.

Failover preserves established sessions only when both provider and application behavior allow it. Applications must tolerate reconnection and duplicate submission. The local gateway assigns an idempotency key to each queued measurement or transaction so a retry does not create a second authoritative record.

## Offline operation and queues

Site gateways store readings and operational transactions locally during a wide-area outage. The offline queue is sized for seven days at the site's approved sampling rate. At 80 percent capacity, the gateway raises a local warning and reduces upload retries; it does not discard newer safety readings to preserve low-value diagnostics.

When the queue reaches capacity, the gateway preserves safety alarms, custody events, and hourly summaries before routine high-frequency telemetry. The site owner documents any aggregation or loss. Local storage is encrypted, and queued restricted data is erased only after the central service confirms durable receipt.

After connectivity returns, the gateway uploads oldest authoritative transactions first while reserving bandwidth for current alarms. It uses content hashes and idempotency keys to reconcile acknowledgements. The dashboard marks backfilled values with their measurement time and receipt time so delayed data are not mistaken for live conditions.

## Monitoring and escalation

The network monitor checks tunnel state, packet loss, latency, link utilization, router health, and queue depth. A total loss of both wide-area links opens a site connectivity incident after five minutes. The on-call engineer confirms whether local safety and recording functions remain available, then contacts the site lead and providers according to impact.

Performance degradation is not judged by latency alone. The engineer compares current values with the site profile and application thresholds. A high-latency satellite link may be healthy for batch telemetry while unsuitable for interactive remote control. Monitoring alerts name the affected function rather than describing every slow link as down.

Site leads can see a local status panel showing link state, last successful central acknowledgement, queue utilization, gateway clock, and active alarms. The panel remains available without wide-area connectivity. Staff report physical damage, power loss, unusual heat, water ingress, or antenna movement instead of repeatedly power-cycling equipment.

## Time and data integrity

Gateways synchronize time from approved sources while online and use a monitored local clock while offline. Records contain measurement time, gateway receipt time, and central receipt time. If clock uncertainty exceeds two minutes, the gateway adds a time-quality flag and the receiving application avoids using exact ordering for a release decision without review.

Message payloads are authenticated and encrypted. The central receiver rejects invalid signatures, but keeps a security event containing the site ID, receipt time, and reason. Field staff never resolve a signature error by disabling verification. A replacement credential follows the site identity procedure.

## Credentials and patching

Each router and gateway has a unique device identity. Site certificates expire after one year and rotate automatically at least 30 days before expiration when connectivity permits. The technical custodian tracks failed rotation and arranges an approved local replacement before the existing certificate expires.

Network Reliability tests firmware in a representative lab before staged deployment. Critical security fixes are scheduled according to risk; ordinary firmware updates occur during the site's maintenance window. A router retains the previous known-good image for rollback. Sites verify local alarming and offline recording after an update, not only central reachability.

Configuration backups are encrypted and stored centrally after every approved change. A configuration file contains sensitive topology and credentials references, so it is restricted information. Field personnel do not exchange router configurations through personal email or consumer file-sharing services.

## Power and environmental protection

Routers, gateways, and essential local displays use conditioned power. Permanent sites provide enough battery runtime for at least 30 minutes so brief interruptions do not corrupt queues or trigger repeated failover. Longer runtime is based on the site safety assessment and generator start plan.

Enclosures maintain manufacturer temperature and moisture limits. Antenna cables have strain relief and surge protection appropriate to the site. Equipment cabinets are not used to store liquids, loose metal hardware, or shipment refrigerants. Environmental alarms remain locally visible even if their central notification path is unavailable.

## Maintenance and changes

Planned changes include a method, expected impact, validation, rollback, owner, and communication window. The site lead confirms that no critical shipment, experiment, or safety operation depends on the planned window. Emergency changes during an incident are recorded in the incident timeline and reconciled into the configuration repository afterward.

Technicians capture baseline signal, latency, packet loss, queue depth, and tunnel state before and after work. A green status lamp alone is insufficient validation. Tests include local sensor publication, central acknowledgement, backup-link failover, and access from an approved managed device.

## Temporary sites and demobilization

A temporary site uses the same segmentation and identity controls as a permanent site, scaled to its risk. The deployment checklist records carrier ownership, data plan, equipment custody, antenna permissions, and emergency contacts. Equipment is not left online after the approved demobilization date without an extension.

At demobilization, Network Reliability revokes site certificates, exports required logs, confirms central queue receipt, erases managed local storage, removes antennas and labels, and updates the asset register. The site owner records unresolved data gaps or damaged equipment. Reusing a router at another site requires a factory reset and a new site identity.

## Records

Network configuration history and change records are retained for three years. Detailed connection logs are retained for 90 days unless attached to an incident or legal hold. Aggregate availability metrics may be retained longer when they do not expose device identifiers or individual activity.
