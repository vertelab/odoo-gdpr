# odoo-gdpr — gren 19.0

> **Denna gren är avsiktligt tom.** Modulerna är INTE portade till Odoo 19.
> Grenen finns så att dev-miljöer (`hansolo19`) kan klona den utan att falla,
> men den påstår ingenting om att koden är portad.

## Baseline

| | |
|---|---|
| Källa | `20.0` |
| Moduler | **2** |
| Grenar i repot | `12.0`, `18.0`, `20.0`, `8.0` |

## Moduler

- `gdpr_inventory`
- `gdpr_inventory_tier_validation`

## Blockerare

**1 externa beroenden saknas** i Odoo 19-kärnan och OCA 19.0:

| Beroende | Behövs av |
|---|---|
| `base_tier_validation` | `gdpr_inventory_tier_validation` |

### Prioritering

Ett beroende som blockerar många moduler ger mest nytta att lösa först:

- `base_tier_validation` — frisläpper **1** modul(er)

## Nästa steg

Portering sker på `*-pfile`-maskin med versionsagnostisk kod
(`.p.py` / `.p.xml`). Se `/skill:odoo-pfiles`.
