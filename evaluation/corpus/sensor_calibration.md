# Meridian Environmental Sensor Calibration Guide

Document ID: MER-LAB-122  
Owner: Measurement Quality  
Revision: 3.0  
Effective date: 2026-02-20

## Scope

This guide controls calibration and field verification for Meridian temperature, humidity, differential-pressure, and carbon-dioxide sensors. It applies to fixed laboratory instruments, cold-chain loggers, and environmental probes installed at remote sites. It does not cover vehicle tire-pressure monitors or consumer devices used only for informal observation.

Calibration establishes the relationship between a sensor's indication and a traceable reference under defined conditions. A field verification is a shorter comparison used to detect drift between calibrations. Passing a field verification does not extend the formal calibration due date unless the device specification explicitly allows an interval based on verified stability.

## Identification and status

Every controlled sensor has an asset ID, manufacturer and model, serial number, measurement range, required accuracy, location, owner, and calibration due date. The status label shows calibrated, verification-only, quarantined, or retired. A missing label does not prove a sensor is out of tolerance, but it prevents use for a release decision until the register is checked.

The asset register is authoritative. Handwritten labels help field work but do not replace register changes. When a sensor moves between a laboratory, vehicle, and remote site, the custodian records its new location and verifies that transport did not exceed the manufacturer's shock, moisture, or temperature limits.

## Intervals

Temperature and humidity sensors used for release decisions are calibrated every 12 months, with a field verification every 90 days. Differential-pressure sensors are calibrated every six months because blockage and membrane aging can cause subtle drift. Carbon-dioxide sensors receive a zero and span verification every 90 days and a full calibration annually.

Measurement Quality may shorten an interval after an out-of-tolerance result, repair, repeated verification drift, harsh deployment, or manufacturer notice. Extending an interval requires at least three consecutive in-tolerance calibrations, a documented stability analysis, and approval from the Measurement Quality lead. No interval may exceed the manufacturer's stated maximum.

## References and environment

Reference instruments must have current calibration traceable to a recognized national measurement institute. The reference uncertainty should be no more than one third of the tolerance being assessed. When that ratio is impractical, the calibration record states the decision rule and expanded uncertainty so users understand the risk near a limit.

Sensors and references equilibrate in the calibration area before readings are taken. The technician records ambient conditions when they could affect the result. Direct sunlight, open loading doors, recently handled probes, and a reference placed against a cold wall can create apparent drift that is actually a poor setup.

## Temperature calibration procedure

Inspect the sensor for damage, contamination, low battery, blocked vents, and an intact seal. Confirm the asset ID and due date. Place the sensor and reference close enough to experience the same stable environment without allowing the devices to touch. For a chamber calibration, use at least three points spanning the normal working range.

At each point, wait until both reference and sensor change by less than 0.1 degrees Celsius over five minutes. Record the reference reading, sensor reading, error, allowed tolerance, and result. For release-decision temperature sensors, the acceptance tolerance is plus or minus 0.5 degrees Celsius at every tested point. Adjust only when the manufacturer provides an approved method, then repeat the complete as-left sequence.

## Humidity and gas checks

Humidity calibration uses certified salt points or a controlled chamber appropriate to the sensor range. Probes require enough stabilization time to avoid accepting a transient value. Condensation invalidates the run; the technician dries the device according to its manual and begins a new sequence after equilibration.

Carbon-dioxide verification uses certified zero gas and a certified span mixture. Tubing material, flow rate, regulator cleanliness, and ambient pressure can change the apparent result. The technician records the gas lot, expiration, certified concentration, and stabilization time. A span result is not corrected by changing software scaling without an approved adjustment record.

## Failed calibration and impact review

Any sensor that fails an as-found calibration is labeled QUARANTINED immediately and removed from release decisions. The technician does not erase or overwrite the as-found results after adjustment. Measurement Quality opens an impact review covering data since the last known acceptable verification or calibration, whichever is later.

The impact review considers maximum observed error, process limits, redundant sensors, environmental history, affected shipments or experiments, and whether the error could change a prior decision. A failed sensor does not automatically invalidate every associated record. The process owner documents which decisions remain supported, which need reanalysis, and which material must remain on hold.

After repair or adjustment, the sensor completes a full as-left calibration. Measurement Quality may return it to service only after reviewing both the calibration and the impact assessment. A sensor with repeated unexplained drift may be restricted to monitoring-only use or retired even when an adjustment can temporarily bring it within tolerance.

## Field verification

A field verification compares a deployed sensor with a portable reference at its operating location. The technician checks placement, airflow, shielding, power, time synchronization, and recent alarms before comparing values. At least three paired readings are taken over 15 minutes under stable conditions.

If the field difference exceeds the verification limit, the deployed sensor is marked suspect and may not support a new release decision. The technician checks for placement and reference problems before removing it. If no setup cause is found, the device enters quarantine and follows the failed-calibration impact process.

Remote sites may complete a field verification while disconnected from the central register. The technician records the signed result locally and uploads it when connectivity returns. Disconnection does not extend a due date, and a locally recorded failure must be acted on immediately rather than waiting for upload.

## Batteries, firmware, and repair

Low battery can bias some measurements before a device stops reporting. Controlled sensors use the approved battery type, and a battery change is recorded with date and technician. A battery change alone does not require calibration, but the technician performs a functional check and confirms that time, units, alarm limits, and logging interval were preserved.

Firmware updates are evaluated as configuration changes. Measurement Quality reviews release notes for changes to compensation, filtering, scaling, timekeeping, or stored data. A functional verification is required after every firmware update; a full calibration is required when measurement behavior could have changed.

Repairs that affect the sensing element, analog path, enclosure airflow, or compensation parameters require full calibration. Cosmetic enclosure repairs may require only inspection and a functional check. Repair vendors return the asset ID and as-found data with the device so history remains continuous.

## Records

Calibration records contain the asset ID, procedure revision, technician, dates, reference IDs, environmental conditions, raw readings, calculations, as-found and as-left results, adjustments, uncertainty where applicable, and approval. The system locks approved records; corrections create an attributed amendment rather than replacing the original value.

Calibration and field-verification records are retained for the life of the sensor plus three years. Impact reviews follow the retention of the affected experiment, shipment, or incident when that period is longer. Exported copies are evidence aids, not independent authoritative records.
