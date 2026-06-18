param(
    [string]$Repo = "palbiez/woocommerce_integration"
)

$ErrorActionPreference = "Stop"

function Test-Gh {
    gh auth status *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "GitHub CLI ist nicht authentifiziert. Bitte zuerst ausfuehren: gh auth login"
    }
}

function Ensure-Label {
    param(
        [string]$Name,
        [string]$Color,
        [string]$Description,
        [array]$Existing
    )

    $exists = $Existing | Where-Object { $_.name -eq $Name }
    if ($exists) {
        gh label edit $Name --repo $Repo --color $Color --description $Description | Out-Null
    }
    else {
        gh label create $Name --repo $Repo --color $Color --description $Description | Out-Null
    }
}

function Ensure-Milestone {
    param(
        [string]$Title,
        [string]$Description,
        [array]$Existing
    )

    $exists = $Existing | Where-Object { $_.title -eq $Title }
    if ($exists) {
        gh api --method PATCH "repos/$Repo/milestones/$($exists.number)" -f title="$Title" -f description="$Description" | Out-Null
    }
    else {
        gh api --method POST "repos/$Repo/milestones" -f title="$Title" -f description="$Description" | Out-Null
    }
}

function Ensure-Issue {
    param(
        [string]$Title,
        [string]$Body,
        [string[]]$Labels,
        [string]$Milestone,
        [array]$ExistingIssues
    )

    $exists = $ExistingIssues | Where-Object { $_.title -eq $Title }
    if ($exists) {
        Write-Host "Issue existiert bereits: $Title"
        return
    }

    $labelArg = $Labels -join ","
    gh issue create --repo $Repo --title $Title --body $Body --label $labelArg --milestone $Milestone | Out-Null
}

Test-Gh

$labels = @(
    @{ Name = "type: requirement"; Color = "0E8A16"; Description = "Fachliche oder technische Anforderung" },
    @{ Name = "type: task"; Color = "1D76DB"; Description = "Konkrete Umsetzungsaufgabe" },
    @{ Name = "type: decision"; Color = "FBCA04"; Description = "Offene Entscheidung" },
    @{ Name = "type: security"; Color = "B60205"; Description = "Sicherheit, Secrets oder Zugriff" },
    @{ Name = "type: docs"; Color = "5319E7"; Description = "Dokumentation" },
    @{ Name = "area: etsy"; Color = "F1641E"; Description = "Etsy API und Etsy Shop" },
    @{ Name = "area: woocommerce"; Color = "96588A"; Description = "WooCommerce und WordPress" },
    @{ Name = "area: n8n"; Color = "EA4B71"; Description = "n8n Automatisierung" },
    @{ Name = "area: dolibarr"; Color = "2B67C6"; Description = "Dolibarr ERP Integration" },
    @{ Name = "area: infra"; Color = "5319E7"; Description = "Server, Deployment und Betrieb" },
    @{ Name = "area: data-model"; Color = "006B75"; Description = "Datenmodell, Mapping und SKUs" },
    @{ Name = "area: orders"; Color = "C2E0C6"; Description = "Bestellungen und Import" },
    @{ Name = "area: fulfillment"; Color = "BFDADC"; Description = "Versand, Tracking und Bestand" },
    @{ Name = "area: monitoring"; Color = "D4C5F9"; Description = "Logging, Alerts und Monitoring" },
    @{ Name = "priority: critical"; Color = "B60205"; Description = "Muss vor produktiver Nutzung geloest werden" },
    @{ Name = "priority: high"; Color = "D93F0B"; Description = "Hohe Prioritaet" },
    @{ Name = "priority: medium"; Color = "FBCA04"; Description = "Mittlere Prioritaet" },
    @{ Name = "priority: low"; Color = "C5DEF5"; Description = "Niedrige Prioritaet" },
    @{ Name = "status: needs-decision"; Color = "FBCA04"; Description = "Blockiert bis zur Entscheidung" },
    @{ Name = "status: blocked"; Color = "E99695"; Description = "Aktuell blockiert" }
)

$existingLabels = gh label list --repo $Repo --limit 200 --json name | ConvertFrom-Json
foreach ($label in $labels) {
    Ensure-Label -Name $label.Name -Color $label.Color -Description $label.Description -Existing $existingLabels
}

$milestones = @(
    @{ Title = "M0 Sicherheit und Projektsetup"; Description = "Git, Secrets, Architekturgrundlage und erste Betriebsentscheidungen." },
    @{ Title = "M1 Etsy Bestandsaufnahme und WooCommerce Migration"; Description = "Bestehendes Etsy Sortiment analysieren und kontrolliert nach WooCommerce migrieren." },
    @{ Title = "M2 Core Sync WooCommerce Etsy"; Description = "Produkt-, Mapping-, Preis- und Listing-Synchronisation von WooCommerce zu Etsy." },
    @{ Title = "M3 Orders Fulfillment und Bestand"; Description = "Bestellungen, Bestand, Bundles, Made-to-Order und Versanddaten synchronisieren." },
    @{ Title = "M4 n8n Betrieb Monitoring"; Description = "n8n Self-Hosting, Benachrichtigungen, Logs, Retry und Betrieb." },
    @{ Title = "M5 Dolibarr Pilotintegration"; Description = "Dolibarr Datenfluss entscheiden und erste API-Anbindung testen." },
    @{ Title = "M6 Produktionsreife"; Description = "Tests, Pilotbetrieb, Monitoring und schrittweise Produktivnahme." }
)

$existingMilestones = gh api "repos/$Repo/milestones?state=all&per_page=100" | ConvertFrom-Json
foreach ($milestone in $milestones) {
    Ensure-Milestone -Title $milestone.Title -Description $milestone.Description -Existing $existingMilestones
}

$existingIssues = gh issue list --repo $Repo --state all --limit 500 --json title,number | ConvertFrom-Json

$issues = @(
    @{
        Title = "[SEC] Zugangsdaten rotieren und Secret-Konzept festlegen"
        Milestone = "M0 Sicherheit und Projektsetup"
        Labels = @("type: security", "area: infra", "priority: critical")
        Body = @"
## Ziel
Alle bereits lokal gespeicherten produktiven Zugangsdaten rotieren und ein Secret-Konzept fuer lokale Entwicklung und Serverbetrieb festlegen.

## Akzeptanzkriterien
- [ ] WordPress App Password wurde rotiert
- [ ] WooCommerce API Key/Secret wurden rotiert
- [ ] Etsy App Secret wurde rotiert
- [ ] SSH-Schluesselstrategie ist dokumentiert
- [ ] `.env.example` enthaelt nur Platzhalter
- [ ] Keine Secrets sind in Git enthalten
"@
    },
    @{
        Title = "[DECISION] Zielarchitektur ohne Docker fuer Start festlegen"
        Milestone = "M0 Sicherheit und Projektsetup"
        Labels = @("type: decision", "area: infra", "priority: high", "status: needs-decision")
        Body = @"
## Entscheidung
Wie wird die eigene Integrationsapp auf dem bestehenden Hetzner-Server betrieben?

## Aktueller Vorschlag
Start ohne Docker: Python venv, systemd Service, Reverse Proxy und separate n8n Installation.

## Akzeptanzkriterien
- [ ] Betriebsmodell ist entschieden
- [ ] Service-User und Verzeichnisstruktur sind definiert
- [ ] Reverse-Proxy- und TLS-Ansatz sind dokumentiert
- [ ] Spaetere Docker-Migration ist als Option dokumentiert
"@
    },
    @{
        Title = "[REQ] SKU- und Produktdatenmodell definieren"
        Milestone = "M1 Etsy Bestandsaufnahme und WooCommerce Migration"
        Labels = @("type: requirement", "area: data-model", "area: woocommerce", "area: etsy", "priority: high")
        Body = @"
## Ziel
Ein stabiles Datenmodell fuer Produkte, Varianten, SKUs, Bundles, Personalisierung und Made-to-Order definieren.

## Akzeptanzkriterien
- [ ] SKU-Regeln fuer einfache Produkte und Varianten sind definiert
- [ ] Bundle-Regeln sind beschrieben
- [ ] Personalisierungsfelder sind beschrieben
- [ ] Made-to-Order-Regeln sind beschrieben
- [ ] Mapping zwischen Etsy Listing und WooCommerce Product ist dokumentiert
"@
    },
    @{
        Title = "[TASK] Bestehende Etsy Listings per API oder Export analysieren"
        Milestone = "M1 Etsy Bestandsaufnahme und WooCommerce Migration"
        Labels = @("type: task", "area: etsy", "area: data-model", "priority: high")
        Body = @"
## Aufgabe
Alle bestehenden Etsy Listings erfassen und technisch auswerten.

## Akzeptanzkriterien
- [ ] Listings, Varianten, Preise und Bilder sind erfasst
- [ ] Personalisierungsoptionen sind erfasst
- [ ] Fehlende oder doppelte SKUs sind identifiziert
- [ ] Sonderfaelle sind dokumentiert
"@
    },
    @{
        Title = "[DECISION] WooCommerce Erweiterung fuer Personalisierungsfelder waehlen"
        Milestone = "M1 Etsy Bestandsaufnahme und WooCommerce Migration"
        Labels = @("type: decision", "area: woocommerce", "area: data-model", "priority: high", "status: needs-decision")
        Body = @"
## Entscheidung
Welche WooCommerce-Erweiterung oder Eigenlogik bildet personalisierte Produktfelder ab?

## Akzeptanzkriterien
- [ ] Kandidaten sind verglichen
- [ ] Export-/API-Zugriff auf Felder ist geklaert
- [ ] Darstellung im Checkout ist geklaert
- [ ] Uebergabe an Etsy/Dolibarr ist bewertet
"@
    },
    @{
        Title = "[DECISION] Bundle-Modell in WooCommerce festlegen"
        Milestone = "M1 Etsy Bestandsaufnahme und WooCommerce Migration"
        Labels = @("type: decision", "area: woocommerce", "area: data-model", "priority: high", "status: needs-decision")
        Body = @"
## Entscheidung
Wie werden Bundles technisch in WooCommerce abgebildet?

## Akzeptanzkriterien
- [ ] Komponentenbestand wird korrekt reduziert
- [ ] Bundle-Preislogik ist klar
- [ ] Etsy-Darstellung ist moeglich
- [ ] Spaetere Dolibarr-Uebergabe ist beruecksichtigt
"@
    },
    @{
        Title = "[DECISION] Made-to-Order Bestand und Lieferzeit definieren"
        Milestone = "M1 Etsy Bestandsaufnahme und WooCommerce Migration"
        Labels = @("type: decision", "area: data-model", "area: fulfillment", "priority: high", "status: needs-decision")
        Body = @"
## Entscheidung
Wie werden Made-to-Order-Produkte bestandsseitig und im Lieferzeitmodell behandelt?

## Akzeptanzkriterien
- [ ] Bestand vs. virtuelle Verfuegbarkeit ist entschieden
- [ ] Produktionszeit ist abbildbar
- [ ] Etsy und WooCommerce zeigen konsistente Informationen
- [ ] Bestellungen koennen sauber priorisiert werden
"@
    },
    @{
        Title = "[TASK] Etsy OAuth und Token-Speicherung als POC bauen"
        Milestone = "M1 Etsy Bestandsaufnahme und WooCommerce Migration"
        Labels = @("type: task", "area: etsy", "area: infra", "priority: high")
        Body = @"
## Aufgabe
OAuth 2.0 Flow fuer Etsy implementieren und Refresh Tokens sicher speichern.

## Akzeptanzkriterien
- [ ] OAuth Flow funktioniert lokal
- [ ] Refresh Token wird sicher gespeichert
- [ ] Shop- und Listingdaten koennen gelesen werden
- [ ] Fehlerfaelle werden geloggt
"@
    },
    @{
        Title = "[TASK] Import-Preview Etsy nach WooCommerce erstellen"
        Milestone = "M1 Etsy Bestandsaufnahme und WooCommerce Migration"
        Labels = @("type: task", "area: etsy", "area: woocommerce", "area: data-model", "priority: high")
        Body = @"
## Aufgabe
Vor dem Schreiben nach WooCommerce eine Vorschau erzeugen, welche Produkte, Varianten und Felder angelegt werden.

## Akzeptanzkriterien
- [ ] Preview zeigt Produktdaten, Varianten, Bilder und Preise
- [ ] Fehlende SKUs werden markiert
- [ ] Sonderfaelle werden markiert
- [ ] Keine WooCommerce-Daten werden ohne Freigabe geschrieben
"@
    },
    @{
        Title = "[TASK] Initialen WooCommerce Produktimport durchfuehren"
        Milestone = "M1 Etsy Bestandsaufnahme und WooCommerce Migration"
        Labels = @("type: task", "area: woocommerce", "area: etsy", "priority: high")
        Body = @"
## Aufgabe
Bestehende Etsy Produkte nach Freigabe kontrolliert in WooCommerce anlegen.

## Akzeptanzkriterien
- [ ] Produkte sind in WooCommerce angelegt
- [ ] Varianten sind korrekt angelegt
- [ ] Bilder sind uebernommen oder verlinkt
- [ ] Etsy Listing IDs sind gespeichert
- [ ] Import ist reproduzierbar dokumentiert
"@
    },
    @{
        Title = "[TASK] Persistente Mapping-Tabelle erstellen"
        Milestone = "M2 Core Sync WooCommerce Etsy"
        Labels = @("type: task", "area: data-model", "area: etsy", "area: woocommerce", "priority: high")
        Body = @"
## Aufgabe
Mapping zwischen WooCommerce Product/Variation IDs und Etsy Listing/Inventory IDs speichern.

## Akzeptanzkriterien
- [ ] Datenbankschema ist definiert
- [ ] IDs werden eindeutig gespeichert
- [ ] SKUs sind validiert
- [ ] Historie oder Sync-Log ist vorgesehen
"@
    },
    @{
        Title = "[TASK] Automatischen Produktabgleich WooCommerce zu Etsy implementieren"
        Milestone = "M2 Core Sync WooCommerce Etsy"
        Labels = @("type: task", "area: woocommerce", "area: etsy", "priority: high")
        Body = @"
## Aufgabe
WooCommerce-Aenderungen automatisch nach Etsy synchronisieren.

## Akzeptanzkriterien
- [ ] Titel, Beschreibung, Preis, Bilder und Bestand werden beruecksichtigt
- [ ] Webhooks oder periodische Jobs sind definiert
- [ ] Doppelte Listings werden verhindert
- [ ] Fehler werden geloggt und koennen wiederholt werden
"@
    },
    @{
        Title = "[DECISION] Preislogik Etsy und WooCommerce festlegen"
        Milestone = "M2 Core Sync WooCommerce Etsy"
        Labels = @("type: decision", "area: data-model", "area: etsy", "area: woocommerce", "priority: medium", "status: needs-decision")
        Body = @"
## Entscheidung
Sollen Etsy-Preise identisch zu WooCommerce sein oder automatisch aufgeschlagen werden?

## Akzeptanzkriterien
- [ ] Preisregel ist fachlich entschieden
- [ ] Rundungsregeln sind definiert
- [ ] Etsy-Gebuehren sind beruecksichtigt
- [ ] Regel ist konfigurierbar umsetzbar
"@
    },
    @{
        Title = "[TASK] Bestandssync mit Idempotenz umsetzen"
        Milestone = "M3 Orders Fulfillment und Bestand"
        Labels = @("type: task", "area: fulfillment", "area: orders", "priority: critical")
        Body = @"
## Aufgabe
Bestand zwischen WooCommerce und Etsy so synchronisieren, dass Events nicht doppelt wirken.

## Akzeptanzkriterien
- [ ] Bestandsaenderungen sind idempotent
- [ ] Bundles reduzieren Komponentenbestand korrekt
- [ ] Made-to-Order wird gesondert behandelt
- [ ] Ueberverkaeufe werden verhindert
- [ ] Konflikte werden protokolliert
"@
    },
    @{
        Title = "[TASK] Etsy Bestellungen nach WooCommerce importieren"
        Milestone = "M3 Orders Fulfillment und Bestand"
        Labels = @("type: task", "area: orders", "area: etsy", "area: woocommerce", "priority: high")
        Body = @"
## Aufgabe
Etsy-Bestellungen nach WooCommerce importieren und eindeutig als Etsy-Ursprung markieren.

## Akzeptanzkriterien
- [ ] Kunden- und Versanddaten werden gemappt
- [ ] Bestellpositionen sind korrekt
- [ ] Personalisierungsdaten werden uebernommen
- [ ] Doppelte Imports werden verhindert
"@
    },
    @{
        Title = "[TASK] Versand- und Trackingdaten zu Etsy synchronisieren"
        Milestone = "M3 Orders Fulfillment und Bestand"
        Labels = @("type: task", "area: fulfillment", "area: etsy", "area: woocommerce", "priority: high")
        Body = @"
## Aufgabe
Trackinginformationen aus WooCommerce an Etsy uebertragen.

## Akzeptanzkriterien
- [ ] Trackingnummer und Carrier werden gelesen
- [ ] Versandstatus wird korrekt gesetzt
- [ ] Bereits versendete Bestellungen werden nicht doppelt gemeldet
- [ ] Fehlerfaelle sind sichtbar
"@
    },
    @{
        Title = "[TASK] Integrationsapp als systemd Service auf Hetzner deployen"
        Milestone = "M4 n8n Betrieb Monitoring"
        Labels = @("type: task", "area: infra", "priority: high")
        Body = @"
## Aufgabe
Die Integrationsapp ohne Docker als systemd Service betreiben.

## Akzeptanzkriterien
- [ ] Nicht-root Service-User ist angelegt
- [ ] Python venv ist eingerichtet
- [ ] systemd Unit ist dokumentiert
- [ ] Reverse Proxy und TLS sind konfiguriert
- [ ] Logs sind auffindbar
"@
    },
    @{
        Title = "[TASK] n8n selbst hosten und absichern"
        Milestone = "M4 n8n Betrieb Monitoring"
        Labels = @("type: task", "area: n8n", "area: infra", "priority: high")
        Body = @"
## Aufgabe
n8n auf dem Hetzner-Server betreiben und absichern.

## Akzeptanzkriterien
- [ ] n8n laeuft als eigener Dienst
- [ ] HTTPS ist aktiv
- [ ] Zugriff ist geschuetzt
- [ ] Credentials sind nicht im Git
- [ ] Backup-Konzept ist dokumentiert
"@
    },
    @{
        Title = "[TASK] Sync-Logs, Retry und Alerts einrichten"
        Milestone = "M4 n8n Betrieb Monitoring"
        Labels = @("type: task", "area: monitoring", "area: n8n", "priority: high")
        Body = @"
## Aufgabe
Fehler und Sync-Vorgaenge nachvollziehbar machen.

## Akzeptanzkriterien
- [ ] Sync-Event-Tabelle oder Logstruktur ist vorhanden
- [ ] Fehlgeschlagene Jobs koennen wiederholt werden
- [ ] Kritische Fehler erzeugen n8n-Benachrichtigung
- [ ] Tagesuebersicht ist moeglich
"@
    },
    @{
        Title = "[DECISION] Dolibarr Datenfluss festlegen"
        Milestone = "M5 Dolibarr Pilotintegration"
        Labels = @("type: decision", "area: dolibarr", "area: data-model", "priority: medium", "status: needs-decision")
        Body = @"
## Entscheidung
Welche Daten sollen zwischen WooCommerce und Dolibarr synchronisiert werden?

## Optionen
1. Nur Bestellungen und Kunden nach Dolibarr
2. Produkte, Kunden und Bestellungen nach Dolibarr
3. Bidirektionale Synchronisation fuer ausgewaehlte Daten

## Akzeptanzkriterien
- [ ] Zielrolle von Dolibarr ist beschrieben
- [ ] Synchronisationsrichtung ist entschieden
- [ ] Dublettenstrategie ist beschrieben
- [ ] Pilotumfang ist festgelegt
"@
    },
    @{
        Title = "[TASK] Dolibarr REST API POC bauen"
        Milestone = "M5 Dolibarr Pilotintegration"
        Labels = @("type: task", "area: dolibarr", "area: infra", "priority: medium")
        Body = @"
## Aufgabe
Dolibarr REST API aktivieren und einen minimalen Datenaustausch testen.

## Akzeptanzkriterien
- [ ] API REST Modul ist aktiv
- [ ] Integrationsuser/API-Key ist vorhanden
- [ ] Produkte oder Kunden koennen gelesen werden
- [ ] Testbestellung oder Testrechnung kann angelegt werden, falls fachlich gewuenscht
"@
    },
    @{
        Title = "[TASK] Pilotbetrieb und Abnahmetests vorbereiten"
        Milestone = "M6 Produktionsreife"
        Labels = @("type: task", "area: monitoring", "area: data-model", "priority: high")
        Body = @"
## Aufgabe
Pilot mit wenigen Produkten vorbereiten und Abnahmetests definieren.

## Akzeptanzkriterien
- [ ] Testfaelle fuer Varianten sind definiert
- [ ] Testfaelle fuer Bundles sind definiert
- [ ] Testfaelle fuer Personalisierung sind definiert
- [ ] Testfaelle fuer Made-to-Order sind definiert
- [ ] Rollback- und Fehlerprozess ist beschrieben
"@
    }
)

foreach ($issue in $issues) {
    Ensure-Issue -Title $issue.Title -Body $issue.Body -Labels $issue.Labels -Milestone $issue.Milestone -ExistingIssues $existingIssues
}

Write-Host "GitHub Tracking Setup abgeschlossen fuer $Repo"

