#!/usr/bin/env python3
"""Build a bundled OpenNumismat collection of Brazilian coins from Colnect.

This is a *headless* builder: it reuses OpenNumismat's existing Colnect import
machinery (the same code path used by the in-app "Import -> Colnect" dialog) to
enumerate every Brazilian coin in the Colnect catalogue and write the records
into a fresh collection database. The resulting file is meant to be committed as
``OpenNumismat/db/brazil_coins.db`` so it ships with the application and can be
opened from "File -> Open built-in Brazilian coins collection".

Requirements (must be satisfied on the machine that runs this script):

* OpenNumismat's runtime dependencies installed (``pip install -r
  requirements.txt``) -- in particular PySide6.
* ``OpenNumismat/private_keys.py`` providing ``COLNECT_PROXY`` and
  ``COLNECT_KEY``. Without it the Colnect importer reports itself unavailable
  and this script cannot fetch anything.
* Outbound network access to the Colnect proxy and image CDN.

The script runs Qt with the ``offscreen`` platform plugin so no display is
needed, and it silences the importer's modal warning dialogs so a rate-limit or
transient error never blocks an unattended run.

Example::

    python3 tools/build_brazil_collection.py \
        --output OpenNumismat/db/brazil_coins.db --since 1800

Re-running with an existing output file requires ``--force`` (the file is
removed and rebuilt from scratch).
"""

import argparse
import os
import sys

# Qt needs a platform plugin even when we never show a window. "offscreen"
# keeps the whole run headless. Set before any PySide6 import.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# Make the OpenNumismat package importable when run from a source checkout.
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


def _find_brazil(countries):
    """Return Colnect's country id for Brazil from a getCountries() result.

    Each entry is ``[id, name, has_coins]``. Match on the localised name; fall
    back to a case-insensitive English/Portuguese spelling.
    """
    for country in countries:
        if len(country) >= 2 and isinstance(country[1], str):
            name = country[1].strip().lower()
            if name in ("brazil", "brasil"):
                return country[0], country[1]
    return None, None


def build(output, since, category, locale):
    from PySide6.QtWidgets import QApplication, QMessageBox

    # A QApplication is required for the Qt SQL / model layer and for the
    # importer's cursor handling, even in offscreen mode.
    app = QApplication.instance() or QApplication(sys.argv)

    # The importer pops modal QMessageBox warnings on API errors / rate limits.
    # In an unattended build those would hang forever, so route them to stderr.
    def _quiet_message(parent=None, title="", text="", *args, **kwargs):
        print(f"[colnect] {title}: {text}", file=sys.stderr)
        return QMessageBox.StandardButton.Ok

    QMessageBox.warning = staticmethod(_quiet_message)
    QMessageBox.critical = staticmethod(_quiet_message)
    QMessageBox.information = staticmethod(_quiet_message)

    import OpenNumismat
    from OpenNumismat.pathes import init_pathes
    init_pathes()

    from OpenNumismat.Settings import Settings
    settings = Settings()
    # Pull catalogue text in the requested language where Colnect supports it.
    settings['colnect_locale'] = locale

    from OpenNumismat.Collection.Import.Colnect import (
        ColnectConnector, colnectAvailable)
    if not colnectAvailable:
        sys.exit(
            "Colnect import is unavailable: create OpenNumismat/private_keys.py "
            "with COLNECT_PROXY and COLNECT_KEY before running this builder.")

    from OpenNumismat.Collection.Collection import Collection

    if os.path.exists(output):
        sys.exit(f"Output already exists: {output} (use --force to overwrite)")

    out_dir = os.path.dirname(os.path.abspath(output))
    os.makedirs(out_dir, exist_ok=True)

    collection = Collection()
    if not collection.create(output):
        sys.exit(f"Could not create collection database at {output}")
    model = collection.model()

    connector = ColnectConnector(None)
    try:
        countries = connector.getCountries("coins")
        country_id, country_name = _find_brazil(countries)
        if country_id is None:
            sys.exit("Could not locate Brazil in Colnect's country list.")
        print(f"Brazil -> Colnect country id {country_id} ({country_name})")

        item_ids = connector.getIds("coins", country_id)
        if not item_ids:
            sys.exit("Colnect returned no Brazilian coins (check keys / limits).")
        print(f"Found {len(item_ids)} Brazilian coin types in the catalogue.")

        fields = connector.getFields("coins")

        added = 0
        skipped_year = 0
        failed = 0
        for i, item_id in enumerate(item_ids, start=1):
            action = f"item/cat/coins/id/{item_id}"
            data = connector.getData(action)
            if not data or len(data) != len(fields):
                failed += 1
                continue

            # makeItem expects the item URL appended as the final column.
            data.append(f"https://colnect.com/{locale}/coins/coin/{item_id}")

            record = model.record()
            connector.makeItem("coins", data, record)

            # "since the 1800s" -- skip anything we can date earlier than --since.
            year = record.value("year")
            try:
                if year not in (None, "") and int(year) < since:
                    skipped_year += 1
                    continue
            except (TypeError, ValueError):
                pass  # keep undated coins

            model.appendRecord(record)
            added += 1

            if i % 50 == 0:
                print(f"  ...processed {i}/{len(item_ids)} "
                      f"(added {added}, skipped {skipped_year}, failed {failed})")

        model.submitAll()
    finally:
        connector.close()

    print(f"Done. Added {added} coins to {output} "
          f"(skipped {skipped_year} pre-{since}, {failed} fetch failures).")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--output", "-o",
        default=os.path.join(REPO_ROOT, "OpenNumismat", "db", "brazil_coins.db"),
        help="Path of the collection database to create "
             "(default: OpenNumismat/db/brazil_coins.db)")
    parser.add_argument(
        "--since", type=int, default=1800,
        help="Skip coins issued before this year (default: 1800)")
    parser.add_argument(
        "--locale", default="en",
        help="Catalogue language passed to Colnect (default: en)")
    parser.add_argument(
        "--force", action="store_true",
        help="Overwrite the output file if it already exists")
    args = parser.parse_args()

    if args.force and os.path.exists(args.output):
        os.remove(args.output)

    build(args.output, args.since, "coins", args.locale)


if __name__ == "__main__":
    main()
