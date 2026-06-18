# WooCommerce-Etsy Integration: Vorschlag

Stand: 18.06.2026

## Ausgangslage

Im Ordner liegen aktuell:

- `anforderungen.md`: fachliche Anforderungen fuer WooCommerce/Etsy
- `config.cfg`: Zugangsdaten und API-Keys
- `hetzner`: privater SSH-Schluessel
- `hetzner.pub`: oeffentlicher SSH-Schluessel

Wichtig: `config.cfg` und `hetzner` duerfen nicht in Git committed werden. Da produktive Zugangsdaten bereits im Klartext gespeichert sind, sollten WordPress-App-Passwort, WooCommerce API-Key/Secret und Etsy-App-Secret vor produktiver Weiterarbeit rotiert werden.

## Zielbild

WooCommerce soll das fuehrende System werden. Etsy ist dann ein Vertriebskanal.

Das bedeutet:

- Produktdaten, Preise, Bestand und interne Artikelstruktur werden in WooCommerce gepflegt.
- Etsy-Listings werden aus WooCommerce heraus erstellt oder aktualisiert.
- Etsy-Bestellungen werden nach WooCommerce importiert.
- Bestandsaenderungen aus beiden Kanaelen werden in WooCommerce konsolidiert.
- Versand-/Trackingdaten werden zwischen WooCommerce und Etsy synchronisiert.
- Die technische Verknuepfung erfolgt ueber stabile IDs: WooCommerce Product-ID, Variation-ID, SKU, Etsy Listing-ID, Etsy Inventory Offering-ID.

## Festgelegte Rahmenbedingungen

- Aktuell existiert nur der Etsy-Shop. WooCommerce muss zuerst aus Etsy-Daten aufgebaut bzw. initial befuellt werden.
- Der Produktumfang liegt aktuell bei ca. 25 Produkten und soll auf ca. 100 Produkte wachsen.
- Es gibt Bundles, personalisierte Produkte und Made-to-Order-Produkte.
- Die Preislogik zwischen Etsy und WooCommerce ist noch offen.
- WooCommerce-Aenderungen sollen spaeter automatisch nach Etsy synchronisiert werden.
- n8n soll selbst auf dem Hetzner-Server laufen.
- Auf dem Hetzner-Server laeuft bereits Dolibarr. Dolibarr soll zukuenftig angebunden werden.
- Docker ist aktuell nicht installiert und soll nicht als zwingende Voraussetzung gesetzt werden.

Konsequenz: Der wichtigste erste Schritt ist nicht der automatische Produkt-Push zu Etsy, sondern der kontrollierte Import des bestehenden Etsy-Sortiments nach WooCommerce inklusive SKU-, Varianten-, Bundle- und Personalisierungsmodell.

## Entscheidung: Eigene Umsetzung

Eine Kauflösung ist keine Option. Die Umsetzung erfolgt als eigene Integrationslösung mit Codex und VS Code.

Sinnvoll, wenn die Integration langfristig ein kontrollierter Kernprozess werden soll oder wenn Standardplugins die benoetigten Regeln nicht sauber abbilden.

Typische Vorteile:

- volle Kontrolle ueber Mapping, Sync-Regeln, Fehlerbehandlung und Datenhaltung
- WooCommerce kann konsequent als fuehrendes System modelliert werden
- eigene Logs, Replays, Monitoring und manuelle Freigaben moeglich
- spaeter erweiterbar auf weitere Kanaele
- private Git-Historie und nachvollziehbare Aenderungen

Typische Nachteile:

- initial deutlich mehr Aufwand
- Etsy OAuth, Listing-/Inventory-API und Variantenlogik muessen sauber implementiert werden
- Betrieb, Monitoring und API-Aenderungen liegen bei euch
- Fehler koennen direkt Umsatz, Bestand und Kundenerfahrung betreffen

Technisch ist eine eigene Umsetzung mit Codex und VS Code sinnvoll, wenn strukturiert gearbeitet wird: kleines Backend, saubere Datenbank, Tests fuer Sync-Regeln, Deployment auf dem Hetzner-Server, Secrets ausserhalb von Git.

## Bewertung: n8n oder aehnliche Automatisierung

n8n ist sinnvoll als Orchestrierungs- und Automatisierungsschicht, aber nicht als alleinige Kernlogik fuer eine robuste WooCommerce/Etsy-Produktintegration.

Geeignet fuer:

- Webhook-Verarbeitung von WooCommerce
- periodische Jobs
- Benachrichtigungen bei Sync-Fehlern
- einfache Datenweitergabe an Slack/E-Mail/Sheets
- manuelle Freigabe-Workflows
- Prototyping einzelner API-Aufrufe

Weniger geeignet fuer:

- komplexes Variantenmapping
- idempotente Produkt-/Bestands-Synchronisation
- Konfliktloesung bei parallelen Bestandsaenderungen
- umfangreiche Retry-/Replay-Logik
- zentrale Datenhaltung fuer Mappingtabellen

Empfehlung: Falls eigene Umsetzung, dann eine kleine eigene Applikation als Kernsystem und optional n8n fuer Randprozesse. Nicht die gesamte Integrationslogik ausschliesslich in n8n bauen.

Quellen:

- Etsy Open API v3: https://developers.etsy.com/
- Etsy OAuth: https://developer.etsy.com/documentation/essentials/authentication
- Etsy Listings Tutorial: https://developer.etsy.com/documentation/tutorials/listings
- WooCommerce REST API: https://developer.woocommerce.com/docs/apis/rest-api/
- WooCommerce Webhooks: https://woocommerce.com/document/webhooks/
- n8n Self-hosting: https://docs.n8n.io/hosting/
- n8n WooCommerce Node: https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.woocommerce/
- Dolibarr REST API Modul: https://wiki.dolibarr.org/index.php/Module_Web_Services_API_REST_(developer)
- Dolibarr-n8n Integration: https://wiki.dolibarr.org/index.php/Integration_of_Dolibarr_to_the_n8n_automation_platform

## Empfehlung

Empfohlener Weg:

1. Bestehendes Etsy-Sortiment zuerst analysieren und nach WooCommerce migrieren.
2. Wegen Bundles, Personalisierungen und Made-to-Order-Produkten eine eigene Mapping- und Sync-Schicht einplanen.
3. WooCommerce nach der Migration als fuehrendes System festlegen.
4. n8n selbst hosten, aber nur fuer Automatisierung, Benachrichtigungen und Nebenprozesse einsetzen.
5. Dolibarr ueber die REST API anbinden, sobald WooCommerce/Etsy stabil laufen.

Bei 25 bis 100 Produkten ist der Umfang klein genug fuer eine kontrollierte eigene Umsetzung, aber gross genug, dass man Mapping, Logs und Fehlerbehandlung von Anfang an sauber bauen sollte.

## Zielarchitektur fuer eigene Umsetzung

Vorschlag:

- Backend: Python 3.13 oder 3.10, z. B. FastAPI fuer Webhooks/API und Celery/RQ/APScheduler fuer Jobs
- Datenbank: PostgreSQL oder vorhandenes MariaDB/MySQL nur dann, wenn es zur Serverlandschaft besser passt
- Cache/Queue: Redis, falls asynchrone Jobs und Retries gebraucht werden; fuer den Start kann ein einfacher Scheduler reichen
- Hosting: Hetzner Linux Server ohne Docker, z. B. Python venv + systemd Service + Reverse Proxy
- Secrets: `.env` oder Server Secret Store, niemals Git
- Logging: strukturierte Logs plus Sync-Event-Tabelle
- Admin-Oberflaeche: zunaechst minimal, spaeter Web-UI fuer Mapping, Fehler und manuelle Freigaben
- n8n: selbst gehostet auf demselben Server, vorzugsweise getrennt als eigener systemd Service oder spaeter als eigener Container, wenn Docker eingefuehrt wird
- Dolibarr: Anbindung ueber REST API nach Aktivierung des Dolibarr-Moduls "API REST"

Alternative mit Docker:

Docker Compose bleibt fuer spaeter sinnvoll, wenn der Server konsolidiert oder neu aufgebaut wird. Fuer den aktuellen Server mit bestehendem Dolibarr ist eine Nicht-Docker-Installation kurzfristig risikoaermer, weil sie weniger in die bestehende Betriebsumgebung eingreift.

## Umsetzungs-Tasks

### Phase 0: Sicherheit und Projektgrundlage

- Git-Repository privat initialisieren.
- `.gitignore` fuer Secrets, SSH-Keys, lokale Environments und Build-Artefakte anlegen.
- Alle bereits gespeicherten produktiven Zugangsdaten rotieren.
- Neues Secret-Konzept definieren: lokale `.env`, produktive Server-Umgebungsvariablen.
- README mit Ziel, Setup und Betriebsannahmen anlegen.
- Entscheidung dokumentieren: eigene App als gesetzter Umsetzungsweg.

### Phase 1: Fachliches Datenmodell

- Bestehendes Etsy-Sortiment exportieren bzw. per API analysieren.
- Ziel-Datenmodell in WooCommerce definieren.
- SKU-Regeln festlegen: einfache Produkte, Varianten, Bundles, Sets.
- Modell fuer personalisierte Produkte definieren: Pflichtfelder, optionale Felder, Freitext, Dateien, Produktionshinweise.
- Modell fuer Made-to-Order definieren: Lieferzeit, Produktionsstatus, Bestand oder virtuelle Verfuegbarkeit.
- Mappingtabelle entwerfen: WooCommerce Product/Variation zu Etsy Listing/Inventory.
- Regeln fuer Preisaufschlaege, Etsy-Gebuehren, Versandprofile und Templates definieren.
- Regeln fuer Konflikte definieren: Was passiert bei Bestand 0, geloeschtem Listing, geaenderter SKU?
- Datenfluss zu Dolibarr fachlich festlegen: Artikel, Kunden, Bestellungen, Rechnungen, Lager oder nur ausgewaehlte Daten.

### Phase 2: API-Grundlagen

- WooCommerce REST API Zugriff testen: Produkte lesen, Bestand lesen, Bestellungen lesen.
- WooCommerce Webhooks einrichten: Produkt geaendert, Bestellung erstellt, Bestellung aktualisiert.
- Etsy OAuth 2.0 Flow implementieren.
- Etsy Token Refresh und sichere Token-Speicherung implementieren.
- Etsy API Zugriff testen: Shop, Listings, Inventory, Orders.
- Dolibarr REST API Modul pruefen bzw. aktivieren.
- Dolibarr API Zugriff testen: Produkte/Services, Dritte/Kunden, Bestellungen oder Rechnungen je nach Zielprozess.

### Phase 3: Etsy-Erstmigration nach WooCommerce

- Etsy Listings, Bilder, Varianten, Preise und Personalisierungsoptionen importieren.
- Import-Preview erstellen, bevor WooCommerce-Produkte angelegt werden.
- SKUs pruefen und fehlende SKUs vergeben.
- WooCommerce-Produkte und Varianten initial anlegen.
- Etsy Listing-IDs und WooCommerce Product-/Variation-IDs dauerhaft verknuepfen.
- Sonderfaelle dokumentieren: Bundle, personalisiertes Produkt, Made-to-Order.
- Nach dem Import WooCommerce als fuehrendes System festlegen.

### Phase 4: Produkt-Synchronisation WooCommerce zu Etsy

- WooCommerce Produktdaten normalisieren.
- Etsy Kategorie-, Attribut- und Template-Mapping bauen.
- Automatische Listing-Aktualisierung implementieren.
- Fuer neue Produkte optional einen Review-Status vor Erstveroeffentlichung vorsehen, auch wenn spaetere Aenderungen automatisch laufen.
- Update-Logik fuer Titel, Beschreibung, Preis, Bestand und Bilder implementieren.
- Deduplizierung ueber SKU und gespeicherte Etsy Listing-ID sicherstellen.
- Preislogik als konfigurierbare Regel bauen, solange identischer Preis vs. Aufschlag noch offen ist.

### Phase 5: Bestand und Bestellungen

- Etsy-Bestellungen nach WooCommerce importieren.
- Kunden- und Versanddaten sauber mappen.
- WooCommerce-Bestellungen aus Etsy eindeutig markieren.
- Bestandsreduktion idempotent umsetzen, damit Events nicht doppelt zaehlen.
- Bestandsabgleich WooCommerce zu Etsy implementieren.
- Optional: Etsy zu WooCommerce Ruecksynchronisation nur fuer relevante Felder erlauben.
- Made-to-Order-Produkte getrennt von physischem Lagerbestand behandeln.
- Bundles so abbuchen, dass Komponentenbestaende korrekt reduziert werden.

### Phase 6: Versand und Tracking

- Versandstatus in WooCommerce auswerten.
- Trackingnummern und Versanddienstleister erfassen.
- Trackingdaten an Etsy uebertragen.
- Fehlerfaelle definieren: fehlender Carrier, ungueltige Trackingnummer, bereits versendet.

### Phase 7: n8n und Automatisierung

- n8n auf dem Hetzner-Server selbst hosten.
- n8n hinter Reverse Proxy und HTTPS betreiben.
- n8n-Dateizugriff und Credentials einschraenken.
- Workflows fuer Fehlerbenachrichtigung, Tagesreports und manuelle Freigaben bauen.
- n8n nicht als primaere Datenhaltung fuer Produkt-/Bestandsmapping verwenden.

### Phase 8: Dolibarr-Anbindung

- Zielrolle von Dolibarr festlegen: ERP, Warenwirtschaft, Rechnung, CRM oder Lager.
- Dolibarr REST API aktivieren und API-Key fuer Integrationsuser erzeugen.
- Datenobjekte mappen: WooCommerce Order zu Dolibarr Bestellung/Rechnung, Kunde zu Third Party, Produkt zu Product/Service.
- Synchronisationsrichtung definieren: WooCommerce zu Dolibarr, Dolibarr zu WooCommerce oder bidirektional.
- Fehler- und Dublettenstrategie fuer Kunden und Artikel definieren.
- Pilot mit wenigen Bestellungen durchfuehren.

### Phase 9: Admin, Monitoring und Betrieb

- Sync-Log und Fehlerliste speichern.
- Retry-Mechanismus fuer fehlgeschlagene API-Aufrufe bauen.
- Manuelle Wiederholung einzelner Sync-Jobs ermoeglichen.
- Monitoring fuer Cronjobs, Queue und API-Fehler einrichten.
- E-Mail/n8n-Benachrichtigung bei kritischen Fehlern bauen.
- Backup-Konzept fuer Datenbank und Konfiguration festlegen.

### Phase 10: Deployment

- Deployment ohne Docker vorbereiten: Python venv, systemd Services, Reverse Proxy, Logrotation.
- Hetzner Server absichern: SSH, Firewall, Updates, nicht-root Deployment-User.
- Reverse Proxy mit TLS einrichten.
- Produktive Umgebungsvariablen setzen.
- Deployment-Dokumentation schreiben.
- Smoke-Test nach Deployment definieren.
- Docker Compose als spaetere Migrationsoption dokumentieren, aber nicht als Startvoraussetzung.

### Phase 11: Tests und Abnahme

- Unit-Tests fuer Mapping- und Sync-Regeln schreiben.
- Integrationstests gegen WooCommerce-Testdaten vorbereiten.
- Etsy-Sandbox bzw. Testmodus soweit moeglich pruefen.
- Testfaelle fuer Varianten, Bestand 0, geloeschte Produkte, doppelte SKUs und API-Fehler ausfuehren.
- Testfaelle fuer Bundles, Personalisierung, Made-to-Order und Teilbestand ausfuehren.
- Pilot mit wenigen Produkten starten.
- Nach erfolgreichem Pilot schrittweise Produktumfang erhoehen.

## Erste Meilensteine

1. Sicherheitsbereinigung und Git-Grundlage.
2. Etsy-Sortiment lesen und Import-Preview erzeugen.
3. WooCommerce Produktmodell fuer Varianten, Bundles, Personalisierung und Made-to-Order definieren.
4. OAuth und Token-Speicherung.
5. Mapping-Datenbank.
6. Initialer Etsy-Import nach WooCommerce.
7. Automatischer Produkt-/Bestandsabgleich WooCommerce zu Etsy.
8. Etsy Order Import nach WooCommerce.
9. Versand-/Tracking-Sync.
10. n8n Self-Hosting und Fehlerbenachrichtigungen.
11. Dolibarr-Pilotintegration.

## Offene Entscheidungen

- Soll Etsy-Preis identisch mit WooCommerce sein oder automatisch aufgeschlagen werden?
- Welche Dolibarr-Daten sollen angebunden werden: Produkte, Kunden, Bestellungen, Rechnungen, Lager?
- Soll Dolibarr nur empfangen oder spaeter auch Daten nach WooCommerce zurueckspielen?
- Welche WooCommerce-Erweiterung wird fuer personalisierte Produktfelder genutzt?
- Wie werden Bundles in WooCommerce technisch abgebildet?
- Wie werden Made-to-Order-Produkte bestandsseitig behandelt?
