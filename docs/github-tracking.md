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

## Reihenfolge innerhalb der Milestones

GitHub Milestones haben keine verlaessliche manuelle Task-Reihenfolge. Deshalb bekommen Issues einen festen Prefix im Titel:

```text
[M1-010] Bestehende Etsy Listings per API oder Export analysieren
[M1-020] SKU- und Produktdatenmodell definieren
[M1-030] Import-Preview Etsy nach WooCommerce erstellen
```

Die Nummern laufen in Zehnerschritten. Dadurch koennen spaeter neue Tasks zwischen bestehende Aufgaben eingefuegt werden, z. B. `M1-025`, ohne alles umzunummerieren.

Arbeitsregel:

- Innerhalb eines Milestones zuerst die kleinste offene Nummer bearbeiten.
- `Decision`-Issues muessen vor abhaengigen `Task`-Issues abgeschlossen werden.
- Kritische Sicherheits- und Datenmodell-Tasks duerfen nicht uebersprungen werden.
- Wenn ein Task blockiert ist, bekommt er `status: blocked`; danach wird der naechste nicht-blockierte Task mit der kleinsten Nummer bearbeitet.
- Ein Milestone gilt erst als bereit fuer den naechsten Milestone, wenn alle kritischen und hohen Tasks abgeschlossen oder bewusst verschoben sind.

## Empfohlene Arbeitsreihenfolge

### M0 Sicherheit und Projektsetup

1. `[M0-010] [SEC] Zugangsdaten rotieren und Secret-Konzept festlegen`
2. `[M0-020] [TASK] README und Projektgrundlage erstellen`
3. `[M0-030] [DECISION] Zielarchitektur ohne Docker fuer Start festlegen`

Ziel: Repository, Secrets und Betriebsgrundlage sind geklaert, bevor produktive APIs oder Deployments genutzt werden.

### M1 Etsy Bestandsaufnahme und WooCommerce Migration

1. `[M1-010] [TASK] WooCommerce REST API Zugriff testen`
2. `[M1-020] [TASK] Etsy OAuth und Token-Speicherung als POC bauen`
3. `[M1-025] [TASK] Etsy OAuth Callback URL registrieren und bereitstellen`
4. `[M1-030] [TASK] Bestehende Etsy Listings per API oder Export analysieren`
5. `[M1-040] [REQ] SKU- und Produktdatenmodell definieren`
6. `[M1-050] [DECISION] WooCommerce Erweiterung fuer Personalisierungsfelder waehlen`
7. `[M1-060] [DECISION] Bundle-Modell in WooCommerce festlegen`
8. `[M1-070] [DECISION] Made-to-Order Bestand und Lieferzeit definieren`
9. `[M1-080] [TASK] Import-Preview Etsy nach WooCommerce erstellen`
10. `[M1-090] [TASK] Initialen WooCommerce Produktimport durchfuehren`

Ziel: Erst lesen und verstehen, dann modellieren, dann previewen, erst danach in WooCommerce schreiben.

### M2 Core Sync WooCommerce Etsy

1. `[M2-010] [TASK] Persistente Mapping-Tabelle erstellen`
2. `[M2-020] [TASK] Etsy Kategorie Attribut und Template Mapping erstellen`
3. `[M2-030] [TASK] WooCommerce Webhooks fuer Produkt und Bestellung einrichten`
4. `[M2-040] [DECISION] Preislogik Etsy und WooCommerce festlegen`
5. `[M2-035] [TASK] Etsy-Webhooks im Developer Portal einrichten`
6. `[M2-050] [TASK] Automatischen Produktabgleich WooCommerce zu Etsy implementieren`
7. `[M2-060] [TASK] Review-Status fuer neue Etsy Listings vorsehen`

Ziel: Erst stabile IDs und Mapping, danach automatische Updates.

### M3 Orders Fulfillment und Bestand

1. `[M3-010] [TASK] Konfliktregeln fuer geloeschte Listings und geaenderte SKUs definieren`
2. `[M3-020] [TASK] Bestandssync mit Idempotenz umsetzen`
3. `[M3-030] [TASK] Etsy Bestellungen nach WooCommerce importieren`
4. `[M3-040] [TASK] Versand- und Trackingdaten zu Etsy synchronisieren`

Ziel: Bestellungen und Bestand duerfen erst automatisiert laufen, wenn doppelte Events und Konflikte beherrscht werden.

### M4 n8n Betrieb Monitoring

1. `[M4-010] [TASK] Integrationsapp als systemd Service auf Hetzner deployen`
2. `[M4-020] [TASK] n8n selbst hosten und absichern`
3. `[M4-030] [TASK] Sync-Logs, Retry und Alerts einrichten`
4. `[M4-040] [TASK] n8n Workflows fuer Benachrichtigung und Tagesreport bauen`

Ziel: Erst lauffaehiger Dienst, dann abgesicherte Automatisierung und Betriebssicht.

### M5 Dolibarr Pilotintegration

1. `[M5-010] [DECISION] Dolibarr Datenfluss festlegen`
2. `[M5-020] [TASK] Dolibarr REST API POC bauen`

Ziel: Dolibarr erst anbinden, wenn klar ist, welche Daten wohin fliessen sollen.

### M6 Produktionsreife

1. `[M6-010] [TASK] Deployment Dokumentation und Smoke Test erstellen`
2. `[M6-020] [TASK] Pilotbetrieb und Abnahmetests vorbereiten`

Ziel: Produktivnahme nur mit dokumentiertem Deployment, Smoke Tests, Pilotumfang und Rollback-Verhalten.

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

```bash
gh auth login
```

Danach:

```bash
pwsh ./scripts/setup-github-tracking.ps1
```

Das Skript legt Labels, Milestones und initiale Issues im Repository `palbiez/woocommerce_integration` an. Bereits vorhandene Labels und Issues mit gleichem Titel werden uebersprungen bzw. aktualisiert.
