# GitHub Tracking

Dieses Repository nutzt GitHub Issues, Labels und Milestones fuer die Anforderungs- und Umsetzungsplanung.

## Moeglich in GitHub Free

GitHub Free reicht fuer dieses Setup aus: private Repositories, Issues, Labels und Milestones koennen fuer ein kleines privates Projekt genutzt werden. GitHub beschreibt Labels als Mittel zur Kategorisierung von Issues und Pull Requests; Milestones dienen zur Fortschrittsverfolgung von Issue-Gruppen.

Quellen:

- https://github.com/pricing
- https://docs.github.com/en/issues/using-labels-and-milestones-to-track-work/managing-labels
- https://docs.github.com/issues/using-labels-and-milestones-to-track-work/about-milestones

## Label-System

Typen:

- `type: requirement`
- `type: task`
- `type: decision`
- `type: security`
- `type: docs`

Bereiche:

- `area: etsy`
- `area: woocommerce`
- `area: n8n`
- `area: dolibarr`
- `area: infra`
- `area: data-model`
- `area: orders`
- `area: fulfillment`
- `area: monitoring`

Prioritaeten:

- `priority: critical`
- `priority: high`
- `priority: medium`
- `priority: low`

Status:

- `status: needs-decision`
- `status: blocked`

## Milestones

1. `M0 Sicherheit und Projektsetup`
2. `M1 Etsy Bestandsaufnahme und WooCommerce Migration`
3. `M2 Core Sync WooCommerce Etsy`
4. `M3 Orders Fulfillment und Bestand`
5. `M4 n8n Betrieb Monitoring`
6. `M5 Dolibarr Pilotintegration`
7. `M6 Produktionsreife`

## Arbeitsweise

- Neue fachliche Anforderungen als `Requirement` erfassen.
- Konkrete Umsetzungsschritte als `Task` erfassen.
- Offene Entscheidungen als `Decision` erfassen und erst danach die abhaengigen Tasks starten.
- Jede Anforderung bekommt mindestens ein Bereichslabel, ein Prioritaetslabel und einen Milestone.
- Secrets, API Keys und SSH-Schluessel bleiben ausserhalb von Git.

## GitHub automatisch einrichten

### Variante A: GitHub Actions

Im Repository gibt es den Workflow `Setup GitHub Tracking`.

Der Workflow kann unter `Actions` manuell gestartet werden und legt Labels, Milestones und initiale Issues direkt in GitHub an. Er nutzt den eingebauten `GITHUB_TOKEN` des Repositories und benoetigt lokal keine `gh` Anmeldung.

### Variante B: Lokal per GitHub CLI

Voraussetzung:

```powershell
gh auth login
```

Danach:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup-github-tracking.ps1
```

Das Skript legt Labels, Milestones und initiale Issues im Repository `palbiez/woocommerce_integration` an. Bereits vorhandene Labels und Issues mit gleichem Titel werden uebersprungen bzw. aktualisiert.
