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
        [string]$Order,
        [string]$Body,
        [string[]]$Labels,
        [string]$Milestone,
        [array]$ExistingIssues
    )

    $desiredTitle = if ([string]::IsNullOrWhiteSpace($Order)) { $Title } else { "[$Order] $Title" }
    $escapedTitle = [regex]::Escape($Title)
    $exists = $ExistingIssues | Where-Object {
        $_.title -eq $desiredTitle -or
        $_.title -eq $Title -or
        $_.title -match "^\[M[0-9]+-[0-9]+\]\s+$escapedTitle$"
    } | Select-Object -First 1

    $bodyWithOrder = if ([string]::IsNullOrWhiteSpace($Order)) {
        $Body
    }
    else {
        "## Reihenfolge`n`n$Order`n`n$Body"
    }

    $labelArg = $Labels -join ","

    if ($exists) {
        Write-Host "Issue existiert bereits, aktualisiere: $desiredTitle"
        gh issue edit $exists.number --repo $Repo --title $desiredTitle --body $bodyWithOrder --milestone $Milestone --add-label $labelArg | Out-Null
        return
    }

    gh issue create --repo $Repo --title $desiredTitle --body $bodyWithOrder --label $labelArg --milestone $Milestone | Out-Null
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
        Order = "M0-010"
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
        Title = "[TASK] README und Projektgrundlage erstellen"
        Order = "M0-020"
        Milestone = "M0 Sicherheit und Projektsetup"
        Labels = @("type: docs", "area: infra", "priority: high")
        Body = @"
## Aufgabe
Projektgrundlage dokumentieren, damit Setup, Zielbild und Betriebsannahmen nachvollziehbar sind.

## Akzeptanzkriterien
- [x] README beschreibt Ziel der Integration
- [x] Lokales Setup ist dokumentiert
- [x] Server-/Deployment-Annahmen sind dokumentiert
- [x] Umgang mit Secrets ist verlinkt
- [x] Link zum Integrationsplan ist enthalten
"@
    },
    @{
        Title = "[DECISION] Zielarchitektur ohne Docker fuer Start festlegen"
        Order = "M0-030"
        Milestone = "M0 Sicherheit und Projektsetup"
        Labels = @("type: decision", "area: infra", "priority: high")
        Body = @"
## Entscheidung
Wie wird die eigene Integrationsapp auf dem bestehenden Hetzner-Server betrieben?

## Aktueller Vorschlag
Start ohne Docker: Python venv, systemd Service, Reverse Proxy und separate n8n Installation.

## Akzeptanzkriterien
- [x] Betriebsmodell ist entschieden
- [x] Service-User und Verzeichnisstruktur sind definiert
- [x] Reverse-Proxy- und TLS-Ansatz ist dokumentiert
- [x] Spaetere Docker-Migration ist als Option dokumentiert
"@
    },
    @{
        Title = "[REQ] SKU- und Produktdatenmodell definieren"
        Order = "M1-040"
        Milestone = "M1 Etsy Bestandsaufnahme und WooCommerce Migration"
        Labels = @("type: requirement", "area: data-model", "area: woocommerce", "area: etsy", "priority: high")
        Body = @"
## Ziel
Ein stabiles Datenmodell fuer Produkte, Varianten, SKUs, Bundles, Personalisierung und Made-to-Order definieren.

## Akzeptanzkriterien
- [x] SKU-Regeln fuer einfache Produkte und Varianten sind definiert
- [x] Bundle-Regeln sind beschrieben
- [x] Personalisierungsfelder sind beschrieben
- [x] Made-to-Order-Regeln sind beschrieben
- [x] Mapping zwischen Etsy Listing und WooCommerce Product ist dokumentiert

## Ergebnis
Entscheidung dokumentiert in `docs/m1-decisions/sku-produktdatenmodell.md`.
"@
    },
    @{
        Title = "[TASK] Bestehende Etsy Listings per API oder Export analysieren"
        Order = "M1-030"
        Milestone = "M1 Etsy Bestandsaufnahme und WooCommerce Migration"
        Labels = @("type: task", "area: etsy", "area: data-model", "priority: high")
        Body = @"
## Aufgabe
Alle bestehenden Etsy Listings erfassen und technisch auswerten.

## Akzeptanzkriterien
- [x] Listings, Varianten, Preise und Bilder werden per API erfasst
- [x] Personalisierungsoptionen werden erfasst
- [x] Fehlende oder doppelte SKUs werden identifiziert
- [x] Sonderfaelle werden dokumentiert

## Ergebnis
Analyse-CLI implementiert; echter Lauf wartet auf die einmalige Etsy-OAuth-Freigabe.
"@
    },
    @{
        Title = "[TASK] Etsy OAuth Callback URL registrieren und bereitstellen"
        Order = "M1-025"
        Milestone = "M1 Etsy Bestandsaufnahme und WooCommerce Migration"
        Labels = @("type: task", "area: etsy", "area: infra", "priority: high")
        Body = @"
## Aufgabe
Eine stabile HTTPS-Callback-Route fuer die Etsy Seller App festlegen, in der Integrationsapp bereitstellen und exakt im Etsy Developer Portal registrieren.

## Abgrenzung
Diese Route ist der OAuth-GET-Ruecksprung fuer `code` und `state`. Sie ist nicht der dauerhafte Etsy-Webhook-Endpoint.

## Akzeptanzkriterien
- [ ] Exakte HTTPS-URL ist festgelegt und in `config.cfg`/Deployment dokumentiert
- [ ] Route akzeptiert `code`, `state` und OAuth-Fehlerparameter
- [ ] `state` wird gegen den gestarteten OAuth-Vorgang geprueft
- [ ] Redirect-URI stimmt bytegenau mit dem Etsy Developer Portal ueberein
- [ ] Callback gibt keine Tokens im Browser oder in Logs aus
- [ ] Callback ist ueber den Reverse Proxy erreichbar und TLS ist aktiv
- [ ] Erfolgreicher Callback speichert Token sicher ausserhalb von Git

## Abhaengigkeiten
Blockiert den echten Abschluss von M1-020 und damit M1-030/M1-080/M1-090.

## Testergebnis 17.09.2026
- URL laut Konfiguration: `https://integration.mrs-daui.de:8443/oauth/etsy/callback`
- Eintrag im Etsy Developer Portal wurde vom Betreiber bestaetigt.
- Externer DNS-Test: `integration.mrs-daui.de` loest auf `78.47.204.164` auf.
- HTTP-Test: Port `8443` ist aktuell nicht erreichbar; Nginx-Konfiguration/Firewall/Service muss auf dem Server aktiviert werden.
"@
    },
    @{
        Title = "[DECISION] WooCommerce Erweiterung fuer Personalisierungsfelder waehlen"
        Order = "M1-050"
        Milestone = "M1 Etsy Bestandsaufnahme und WooCommerce Migration"
        Labels = @("type: decision", "area: woocommerce", "area: data-model", "priority: high", "status: needs-decision")
        Body = @"
## Entscheidung
Welche WooCommerce-Erweiterung oder Eigenlogik bildet personalisierte Produktfelder ab?

## Akzeptanzkriterien
- [x] Kandidaten sind verglichen
- [ ] Export-/API-Zugriff auf Felder ist geklaert (Shop-Test mit Plugin steht noch aus)
- [x] Darstellung im Checkout ist geklaert
- [x] Uebergabe an Etsy/Dolibarr ist bewertet
"@
    },
    @{
        Title = "[DECISION] Bundle-Modell in WooCommerce festlegen"
        Order = "M1-060"
        Milestone = "M1 Etsy Bestandsaufnahme und WooCommerce Migration"
        Labels = @("type: decision", "area: woocommerce", "area: data-model", "priority: high", "status: needs-decision")
        Body = @"
## Entscheidung
Wie werden Bundles technisch in WooCommerce abgebildet?

## Akzeptanzkriterien
- [ ] Komponentenbestand wird korrekt reduziert (M3-Aufgabe)
- [x] Bundle-Preislogik ist klar
- [x] Etsy-Darstellung ist moeglich
- [x] Spaetere Dolibarr-Uebergabe ist beruecksichtigt
"@
    },
    @{
        Title = "[DECISION] Made-to-Order Bestand und Lieferzeit definieren"
        Order = "M1-070"
        Milestone = "M1 Etsy Bestandsaufnahme und WooCommerce Migration"
        Labels = @("type: decision", "area: data-model", "area: fulfillment", "priority: high", "status: needs-decision")
        Body = @"
## Entscheidung
Wie werden Made-to-Order-Produkte bestandsseitig und im Lieferzeitmodell behandelt?

## Akzeptanzkriterien
- [x] Bestand vs. virtuelle Verfuegbarkeit ist entschieden
- [x] Produktionszeit ist abbildbar
- [x] Etsy und WooCommerce zeigen konsistente Informationen
- [x] Bestellungen koennen sauber priorisiert werden
"@
    },
    @{
        Title = "[TASK] Etsy OAuth und Token-Speicherung als POC bauen"
        Order = "M1-020"
        Milestone = "M1 Etsy Bestandsaufnahme und WooCommerce Migration"
        Labels = @("type: task", "area: etsy", "area: infra", "priority: high")
        Body = @"
## Aufgabe
OAuth 2.0 Flow fuer Etsy implementieren und Refresh Tokens sicher speichern.

## Akzeptanzkriterien
- [x] OAuth Flow ist als PKCE-CLI implementiert
- [x] Refresh Token wird sicher unter `.secrets/etsy_token.json` mit Dateirechten 0600 gespeichert
- [ ] Shop- und Listingdaten koennen gelesen werden (offen: einmalige Browserfreigabe erforderlich)
- [x] Fehlerfaelle werden ohne Secretwerte ausgegeben

## Ergebnis
Technischer POC implementiert. Die aktuellen Seller-App-Credentials wurden geprueft; der API-Key funktioniert. OAuth-Link mit der registrierten Redirect-URI wurde am 17.09.2026 erzeugt. Die Token-Erzeugung bleibt offen, bis DNS/HTTPS fuer M1-025 erreichbar ist.
"@
    },
    @{
        Title = "[TASK] WooCommerce REST API Zugriff testen"
        Order = "M1-010"
        Milestone = "M1 Etsy Bestandsaufnahme und WooCommerce Migration"
        Labels = @("type: task", "area: woocommerce", "area: infra", "priority: high")
        Body = @"
## Aufgabe
WooCommerce REST API Zugriff fuer Produkte, Varianten, Bestand und Bestellungen testen.

## Akzeptanzkriterien
- [x] Produktliste kann gelesen werden (16.09.2026: API erreichbar, 0 Produkte)
- [x] Einzelnes Produkt kann gelesen werden (bei leerem Shop nicht anwendbar)
- [x] Varianten koennen gelesen werden (bei leerem Shop nicht anwendbar)
- [x] Bestand kann gelesen werden
- [x] Bestellungen koennen gelesen werden (16.09.2026: 0 Bestellungen)
- [x] Authentifizierung ist ohne Klartext-Secrets im Code geloest

## Ergebnis
WooCommerce REST API erfolgreich verifiziert; Report liegt lokal unter `data/m1_woocommerce_check/` und wird nicht versioniert.
"@
    },
    @{
        Title = "[TASK] WooCommerce Webhooks fuer Produkt und Bestellung einrichten"
        Order = "M2-030"
        Milestone = "M2 Core Sync WooCommerce Etsy"
        Labels = @("type: task", "area: woocommerce", "area: infra", "priority: high")
        Body = @"
## Aufgabe
WooCommerce Webhooks fuer Produkt- und Bestellaenderungen vorbereiten.

## Akzeptanzkriterien
- [ ] Produkt geaendert Webhook ist definiert
- [ ] Bestellung erstellt Webhook ist definiert
- [ ] Bestellung aktualisiert Webhook ist definiert
- [ ] Signatur-/Authentifizierungskonzept ist dokumentiert
- [ ] Testpayloads werden geloggt
"@
    },
    @{
        Title = "[TASK] Etsy-Webhooks im Developer Portal einrichten"
        Order = "M2-035"
        Milestone = "M2 Core Sync WooCommerce Etsy"
        Labels = @("type: task", "area: etsy", "area: infra", "area: orders", "priority: high")
        Body = @"
## Aufgabe
Den dauerhaft erreichbaren Etsy-Webhook-Endpoint bereitstellen und im Etsy Webhook Portal fuer die Seller App konfigurieren.

## Abgrenzung
Der OAuth-Callback aus M1-025 ist eine separate Route. Dieser Endpoint nimmt signierte HTTP-POST-Nachrichten entgegen.

## Akzeptanzkriterien
- [ ] Oeffentliche HTTPS-URL fuer Etsy-Webhooks ist festgelegt und dokumentiert
- [ ] Endpoint akzeptiert die aktuell benoetigten Events: `order.paid`, `order.canceled`, `order.shipped`, `order.delivered`
- [ ] Etsy-Webhooks sind im Developer/Webhook Portal angelegt und der Status ist dokumentiert
- [ ] Signing Secret liegt ausserhalb von Git und wird aus produktiver Konfiguration geladen
- [ ] Signatur wird anhand des Raw-Request-Bodys und der Header `webhook-id`, `webhook-timestamp`, `webhook-signature` geprueft
- [ ] Ungueltige oder zu alte Requests werden abgewiesen
- [ ] Wiederholte Zustellungen werden ueber `webhook-id` idempotent behandelt
- [ ] Testevents aus dem Etsy Webhook Portal sind erfolgreich verarbeitet

## Abhaengigkeiten
M2-035 stellt die technische Zustellung sicher; M3-030 verarbeitet die Etsy-Bestellung fachlich in WooCommerce.
"@
    },
    @{
        Title = "[TASK] Import-Preview Etsy nach WooCommerce erstellen"
        Order = "M1-080"
        Milestone = "M1 Etsy Bestandsaufnahme und WooCommerce Migration"
        Labels = @("type: task", "area: etsy", "area: woocommerce", "area: data-model", "priority: high")
        Body = @"
## Aufgabe
Vor dem Schreiben nach WooCommerce eine Vorschau erzeugen, welche Produkte, Varianten und Felder angelegt werden.

## Akzeptanzkriterien
- [x] Preview zeigt Produktdaten, Varianten, Bilder und Preise
- [x] Fehlende SKUs werden markiert
- [x] Sonderfaelle werden markiert
- [x] Keine WooCommerce-Daten werden ohne Freigabe geschrieben

## Ergebnis
Preview-CLI implementiert und per Fixture-Test verifiziert; echter Etsy-Lauf wartet auf OAuth.
"@
    },
    @{
        Title = "[TASK] Initialen WooCommerce Produktimport durchfuehren"
        Order = "M1-090"
        Milestone = "M1 Etsy Bestandsaufnahme und WooCommerce Migration"
        Labels = @("type: task", "area: woocommerce", "area: etsy", "priority: high")
        Body = @"
## Aufgabe
Bestehende Etsy Produkte nach Freigabe kontrolliert in WooCommerce anlegen.

## Akzeptanzkriterien
- [ ] Produkte sind in WooCommerce angelegt (Etsy-Analyse/Preview wartet auf OAuth)
- [x] Varianten werden korrekt angelegt und bei Wiederholung per SKU aktualisiert
- [x] Bilder werden uebernommen oder verlinkt
- [x] Etsy Listing IDs werden gespeichert
- [x] Import ist reproduzierbar dokumentiert und gegen Duplikate abgesichert

## Ergebnis
Kontrollierter Dry-Run/Apply-Importer implementiert. Produktiver Lauf wartet auf Etsy-OAuth, Preview und SKU-Freigabe.
"@
    },
    @{
        Title = "[TASK] Etsy Kategorie Attribut und Template Mapping erstellen"
        Order = "M2-020"
        Milestone = "M2 Core Sync WooCommerce Etsy"
        Labels = @("type: task", "area: etsy", "area: data-model", "priority: high")
        Body = @"
## Aufgabe
Mapping fuer Etsy Kategorien, Attribute, Versandprofile und Listing-Templates definieren.

## Akzeptanzkriterien
- [ ] Kategorien der bestehenden Listings sind erfasst
- [ ] Pflichtattribute je Kategorie sind dokumentiert
- [ ] Versandprofile sind zugeordnet
- [ ] Template-Regeln fuer Titel und Beschreibung sind definiert
- [ ] Mapping ist versionierbar abgelegt
"@
    },
    @{
        Title = "[TASK] Persistente Mapping-Tabelle erstellen"
        Order = "M2-010"
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
        Order = "M2-050"
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
        Title = "[TASK] Review-Status fuer neue Etsy Listings vorsehen"
        Order = "M2-060"
        Milestone = "M2 Core Sync WooCommerce Etsy"
        Labels = @("type: task", "area: etsy", "area: woocommerce", "priority: medium")
        Body = @"
## Aufgabe
Fuer neue Produkte einen kontrollierten Erstveroeffentlichungsprozess vorsehen, waehrend spaetere Aenderungen automatisch synchronisieren.

## Akzeptanzkriterien
- [ ] Neue Produkte koennen als Review erforderlich markiert werden
- [ ] Bestehende verknuepfte Listings werden automatisch aktualisiert
- [ ] Status ist im Mapping sichtbar
- [ ] Fehlerhafte Erstveroeffentlichungen erzeugen keinen doppelten Etsy-Eintrag
"@
    },
    @{
        Title = "[DECISION] Preislogik Etsy und WooCommerce festlegen"
        Order = "M2-040"
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
        Order = "M3-020"
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
        Title = "[TASK] Konfliktregeln fuer geloeschte Listings und geaenderte SKUs definieren"
        Order = "M3-010"
        Milestone = "M3 Orders Fulfillment und Bestand"
        Labels = @("type: task", "area: data-model", "area: etsy", "area: woocommerce", "priority: high")
        Body = @"
## Aufgabe
Regeln definieren, wie die Integration bei geloeschten Etsy Listings, geaenderten SKUs, Bestand 0 und nicht mehr auffindbaren Produkten reagiert.

## Akzeptanzkriterien
- [ ] Regel fuer geloeschte Etsy Listings ist definiert
- [ ] Regel fuer SKU-Aenderungen ist definiert
- [ ] Regel fuer Bestand 0 ist definiert
- [ ] Regel fuer nicht auffindbare WooCommerce-Produkte ist definiert
- [ ] Konflikte werden nicht still automatisch ueberschrieben
"@
    },
    @{
        Title = "[TASK] Etsy Bestellungen nach WooCommerce importieren"
        Order = "M3-030"
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
        Order = "M3-040"
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
        Title = "[TASK] n8n Workflows fuer Benachrichtigung und Tagesreport bauen"
        Order = "M4-040"
        Milestone = "M4 n8n Betrieb Monitoring"
        Labels = @("type: task", "area: n8n", "area: monitoring", "priority: medium")
        Body = @"
## Aufgabe
n8n fuer operative Benachrichtigungen und Tagesreports einsetzen.

## Akzeptanzkriterien
- [ ] Kritische Sync-Fehler erzeugen eine Benachrichtigung
- [ ] Tagesreport fuer erfolgreiche und fehlgeschlagene Jobs ist definiert
- [ ] Manuelle Freigabe-Workflows sind nur fuer definierte Sonderfaelle vorgesehen
- [ ] n8n speichert keine primaeren Mapping-Daten
"@
    },
    @{
        Title = "[TASK] Integrationsapp als systemd Service auf Hetzner deployen"
        Order = "M4-010"
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
        Order = "M4-020"
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
        Order = "M4-030"
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
        Order = "M5-010"
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
        Order = "M5-020"
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
        Title = "[TASK] Deployment Dokumentation und Smoke Test erstellen"
        Order = "M6-010"
        Milestone = "M6 Produktionsreife"
        Labels = @("type: docs", "area: infra", "priority: high")
        Body = @"
## Aufgabe
Deployment-Schritte, Umgebungsvariablen und Smoke Tests dokumentieren.

## Akzeptanzkriterien
- [ ] Deployment ohne Docker ist Schritt fuer Schritt dokumentiert
- [ ] systemd Restart und Logzugriff sind dokumentiert
- [ ] Reverse Proxy und TLS sind dokumentiert
- [ ] Smoke Test fuer WooCommerce API ist definiert
- [ ] Smoke Test fuer Etsy API ist definiert
- [ ] Rollback-Vorgehen ist beschrieben
"@
    },
    @{
        Title = "[TASK] Pilotbetrieb und Abnahmetests vorbereiten"
        Order = "M6-020"
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
    Ensure-Issue -Title $issue.Title -Order $issue.Order -Body $issue.Body -Labels $issue.Labels -Milestone $issue.Milestone -ExistingIssues $existingIssues
}

Write-Host "GitHub Tracking Setup abgeschlossen fuer $Repo"
