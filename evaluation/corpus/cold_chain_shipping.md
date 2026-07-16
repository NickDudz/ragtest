# Meridian Cold-Chain Shipping Procedure

Document ID: MER-LOG-330  
Owner: Research Logistics  
Revision: 4.3  
Effective date: 2026-05-25

## Scope

This procedure controls preparation, transport, receipt, and disposition of Meridian Research Cooperative material that must remain between 2 and 8 degrees Celsius. It covers research reagents, non-clinical specimens, and calibrated reference material identified by a shipment plan. Material requiring frozen, cryogenic, dangerous-goods, or clinical handling follows a specialized procedure instead.

The shipment owner approves the route, acceptable transit time, packaging qualification, recipients, and excursion decision maker. The packer verifies material identity and packaging. The courier controls physical custody in transit. The recipient inspects and acknowledges delivery. One person may perform more than one role at a small site, but each required check remains recorded.

## Shipment plan

Every controlled shipment has a unique shipment ID. The plan lists contents, quantity, classification, origin, destination, contacts, expected handoffs, acceptable temperature range, qualified package configuration, logger IDs, planned departure and arrival, maximum transit duration, and contingency route. The plan also states whether material may be replaced or whether it is unique.

The owner checks weather, service advisories, holidays, receiving hours, and customs needs before release. A route that is normally next-day is not assumed suitable when the destination will be closed. Shipments are not left in an unattended reception area unless the qualified route and recipient agreement explicitly permit it.

## Packaging preparation

Only a package configuration qualified for the season, route duration, payload, and coolant type is used. The packer inspects the outer container, insulation, coolant, absorbent material, secondary containment, seals, and labels. Substituting a larger box, different gel pack, or untested payload arrangement can change thermal performance and requires owner approval.

Conditioned refrigerant packs are arranged according to the qualification diagram. Material that can be damaged by freezing is separated from direct refrigerant contact by the specified barrier. Empty space is filled only with the qualified material and pattern; loose paper or an improvised blanket can create air channels and inconsistent temperatures.

The packer records package lot or identifier, coolant conditioning start and finish, material condition, packing start and seal time, and any deviation. Photographs document the final internal arrangement for unique or high-value material without exposing restricted labels beyond the controlled record.

## Temperature loggers

Each shipment uses at least one approved logger with current calibration. For standard parcels, the primary logger is placed beside the payload at the thermal center of the package, not directly against a refrigerant pack or outer wall. Large qualified containers use the number and positions specified by their qualification study.

Before packing, the packer confirms logger ID, calibration due date, battery status, clock, units, sample interval, and alarm limits. The logger is started early enough to show a stable pre-shipment reading. A display that shows a plausible temperature does not replace downloading the logger record after receipt.

The default logging interval is five minutes. A different interval must still capture excursions relevant to the material and fit within logger memory for the maximum transit duration. Logger time is recorded in UTC or with an explicit offset so handoff and temperature events can be aligned.

## Release and custody

The packer verifies the sealed package against the shipment plan and signs the release. The first courier records pickup time and package condition. Every custody transfer records the shipment ID, releasing person or organization, receiving person or organization, time, location, and visible package condition.

A tracking scan may support a custody record but does not replace a required named handoff when the plan calls for one. If a courier uses a subcontractor, the contracted courier remains responsible for obtaining traceable movement and exception information.

The shipping label uses the minimum necessary contact and handling information. Detailed contents, research notes, or participant information are not placed on the outer package. Restricted electronic records are shared with the recipient through an approved system, not attached to an unencrypted carrier email.

## In-transit monitoring and delay

Where live telemetry is available, Research Logistics monitors temperature alarms, location, and predicted arrival. Lack of live telemetry is not itself an excursion if the logger continues recording. A connectivity gap is noted, and the complete logger history is reviewed at receipt.

For a delay, the logistics coordinator determines remaining qualified duration, package location, facility conditions, recipient availability, and options for priority movement or controlled re-icing. A package is not opened or re-iced by an unqualified carrier depot. Any authorized intervention records new seals, coolant, conditions, personnel, and time.

If the qualified duration may expire before delivery, the coordinator informs the shipment owner and recipient. They may redirect to an approved intermediate facility, arrange validated replenishment, return the package, or hold it for disposition. Cost alone does not justify continuing a route that can no longer support the required condition.

## Receipt

The recipient records arrival time before opening, photographs material damage when present, and compares the seal and shipment ID with the plan. The recipient then opens the package promptly in an appropriate area, stops or marks the logger, checks payload condition, and moves material to approved storage.

The logger data are downloaded without altering the original file. The recipient records the file hash, logger ID, time zone, observed minimum and maximum, and any alarm. For a normal shipment, the owner or delegate reviews the graph for gaps, implausible steps, clock error, or exposure hidden by a simple minimum-maximum summary.

## Excursions and disposition

Any reading below 2 degrees Celsius or above 8 degrees Celsius is a temperature excursion and places the material on HOLD pending documented assessment. A missing logger record, unqualified package substitution, broken seal, unknown custody interval, or transit beyond qualified duration also triggers hold even when an available temperature display appears normal.

Held material is segregated and labeled so it cannot be used accidentally. The shipment owner gathers duration and magnitude of the excursion, logger uncertainty, material stability data, package history, custody information, and any evidence of freezing or damage. The owner may consult Measurement Quality, the material expert, or the supplier.

Disposition is release, restricted use, rework, return, or disposal. The authorized decision maker records the evidence and rationale; a courier's statement that the package felt cold is not release evidence. Unique material is not automatically released because replacement is difficult, and replaceable material is not automatically discarded without assessment.

If a logger itself appears faulty, it enters the sensor quarantine and impact-review process. A comparison with a second logger may support the assessment, but no one edits the original record to remove an inconvenient reading.

## Records and retention

The complete shipment record includes the approved plan, packing checklist, qualification reference, custody transfers, tracking history, logger file and hash, receipt inspection, deviations, communications, and disposition. Cold-chain shipment records are retained for two years after delivery or final disposal. A legal hold or research plan may require longer preservation.

Electronic records use the shipment ID and restricted access where contents or partner details require it. Paper custody forms are scanned into the authoritative record and then destroyed through the approved confidential process after verification. Working copies are removed when the record is complete.

## Training and quality review

Packers and receivers complete initial practical training and annual refresher training. The practical check includes logger setup, qualified packing, custody documentation, download, and excursion hold. Couriers receive handling instructions appropriate to their role but do not make scientific disposition decisions.

Research Logistics reviews a sample of completed shipments quarterly. The review looks for complete custody, correct package configuration, calibrated logger use, unexplained data gaps, timely receipt, and supported disposition. Repeated deviations create corrective work and may suspend a route or package configuration until effectiveness is demonstrated.
