from __future__ import annotations

import argparse
from pathlib import Path

from common import PROJECT_ROOT, main_guard


TEMPLATES = {
    "sku-produktdatenmodell.md": """# M1-040 SKU- und Produktdatenmodell

## Ziel

Ein stabiles Datenmodell fuer Produkte, Varianten, SKUs, Bundles, Personalisierung und Made-to-Order.

## SKU-Regeln

- Einfache Produkte:
- Varianten:
- Bundle-Komponenten:
- Fehlende Etsy-SKUs:

## Mapping

| WooCommerce | Etsy | Zweck |
| --- | --- | --- |
| Product ID | Listing ID | Produktverknuepfung |
| Variation ID | Inventory Product/Offering ID | Variantenverknuepfung |
| SKU | SKU | Fachlicher stabiler Schluessel |

## Offene Punkte

- [ ] ...
""",
    "personalisierungsfelder.md": """# M1-050 WooCommerce Erweiterung fuer Personalisierungsfelder

## Entscheidung

Welche WooCommerce-Erweiterung oder Eigenlogik bildet personalisierte Produktfelder ab?

## Kandidaten

| Kandidat | Checkout-Darstellung | API-Zugriff | Exportfaehigkeit | Bewertung |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

## Entscheidung

- Gewaehlter Ansatz:
- Begruendung:
- Risiken:
""",
    "bundle-modell.md": """# M1-060 Bundle-Modell in WooCommerce

## Entscheidung

Wie werden Bundles technisch in WooCommerce abgebildet?

## Anforderungen

- Komponentenbestand wird korrekt reduziert
- Bundle-Preislogik ist klar
- Etsy-Darstellung bleibt moeglich
- Spaetere Dolibarr-Uebergabe ist beruecksichtigt

## Entscheidung

- Gewaehlter Ansatz:
- Begruendung:
- Risiken:
""",
    "made-to-order.md": """# M1-070 Made-to-Order Bestand und Lieferzeit

## Entscheidung

Wie werden Made-to-Order-Produkte bestandsseitig und im Lieferzeitmodell behandelt?

## Regeln

- Bestand vs. virtuelle Verfuegbarkeit:
- Produktionszeit:
- Priorisierung von Bestellungen:
- Darstellung in WooCommerce:
- Darstellung in Etsy:

## Entscheidung

- Gewaehlter Ansatz:
- Begruendung:
- Risiken:
""",
}


def run() -> None:
    parser = argparse.ArgumentParser(
        description="M1 Decision-Templates fuer Datenmodell, Personalisierung, Bundles und Made-to-Order erstellen."
    )
    parser.add_argument("--out-dir", default=str(PROJECT_ROOT / "docs" / "m1-decisions"))
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for filename, content in TEMPLATES.items():
        path = out_dir / filename
        if path.exists():
            print(f"Vorhanden, nicht ueberschrieben: {path}")
            continue
        path.write_text(content, encoding="utf-8")
        print(f"Erstellt: {path}")


if __name__ == "__main__":
    main_guard(run)
