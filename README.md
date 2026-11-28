# odoo-gdpr

Privacy program management for the General Data Protection Regulation (GDPR).

## Modules

| Module | Purpose |
|---|---|
| `gdpr_inventory` | Record of processing activities (Art. 30), consent register, retention rules |
| `gdpr_inventory_tier_validation` | Tier validation on the inventory before it can be activated |

## What `gdpr_inventory` does

- **Inventory of processing activities** — one record per processing activity,
  with the fields Article 30.1 requires: controller and DPO, purposes,
  categories of data subjects and personal data, recipient categories,
  third-country transfers with safeguards, retention limits, and security
  measures.
- **Consent register** — who consented, when, and when it was withdrawn
  (Art. 7). Withdrawal is recorded as a state change with a chatter message.
- **Retention and automatic restriction** — an inventory declares a domain and
  a restriction method. A daily cron flags matching records and then applies
  the method: erase, hide (archive), pseudonymise, manual, or custom code.
- **Purpose scoping** — every inventory carries a purpose (legal basis), and
  the purpose follows into the object, consent and partner drill-downs so a
  list always says *why* the records are processed.
- **Restriction log** — every restriction writes a `gdpr.log` entry *before*
  the data is changed, so an interrupted run can be inspected.

## What `gdpr_inventory` does not do

- **`encrypt` is not implemented.** The restriction type exists in the
  selection, but selecting it raises a clear error instead of silently doing
  nothing. Encryption of personal data fields is a separate concern.
- **No document storage.** Processing agreements, DPIAs and policies belong in
  the DMS (`dms_gdpr`), not here.
- **No signature.** Signed consents and agreements belong in `sign_gdpr`.
- **No data subject portal.** The portal (`gdpr_portal`) reads the inventory;
  it is not part of this module.
- **No AI assistance.** `gdpr_ai` is parked; see
  `openspec/changes/gdpr-18-repair-and-extend/design.md` (D7).

## Retention safety

Restriction never deletes on the first run:

1. A new inventory defaults to `dry_run = True`. The cron logs what *would* be
   restricted and changes nothing.
2. When dry run is switched off, matching objects are flagged `restricted` and
   a `gdpr.log` entry is written **before** any record is touched.
3. Each object is then restricted inside its own savepoint. A failure on one
   record does not abort the batch; it is logged and the next record runs.
4. Erase and hide are executed through Odoo's `data_recycle` mechanism, not a
   bespoke deletion routine.

**Consent-based processing is only restricted when the consent is withdrawn.**
If the inventory's legal basis is consent, `_get_restrict_objects()` restricts
only objects whose consent state is `withdrawn`. An inventory with a consent
basis and no withdrawn consents therefore restricts nothing — by design.

## Requirements

- Odoo 18.0
- `mail`, `document_page`, `data_recycle`
