# Brazilian coins collection

OpenNumismat is a collection *manager*: it does not ship catalogue data of its
own. To make a ready-to-use set of Brazilian coins available out of the box, a
bundled collection database can be generated from the
[Colnect](https://colnect.com/) catalogue using the existing in-app importer,
then committed so it ships with the application.

## How it works

* `tools/build_brazil_collection.py` is a **headless** builder. It reuses the
  exact code path behind the in-app *File → Import → Colnect* dialog
  (`ColnectConnector`): it looks up Brazil's Colnect country id, enumerates
  every Brazilian coin type, fetches each one, and writes the records into a new
  collection database.
* The output is intended to be committed as
  `OpenNumismat/db/brazil_coins.db`. The whole `OpenNumismat/db` folder is
  already included by the build specs (`open-numismat.spec`, `setup.py`), so no
  packaging changes are needed.
* In the app, **File → Open built-in Brazilian coins collection** copies the
  bundled database into the user's home folder (so it stays editable) and opens
  it.

## Generating the database

The builder must run on a machine that has:

1. OpenNumismat's runtime dependencies (`pip install -r requirements.txt`),
   notably PySide6.
2. `OpenNumismat/private_keys.py` providing `COLNECT_PROXY` and `COLNECT_KEY`.
   Without it the Colnect importer reports itself unavailable.
3. Outbound network access to the Colnect proxy and image CDN.

```sh
python3 tools/build_brazil_collection.py \
    --output OpenNumismat/db/brazil_coins.db \
    --since 1800
```

Options:

| Option      | Default                          | Meaning                                   |
| ----------- | -------------------------------- | ----------------------------------------- |
| `--output`  | `OpenNumismat/db/brazil_coins.db`| Collection database to create             |
| `--since`   | `1800`                           | Skip coins issued before this year        |
| `--locale`  | `en`                             | Catalogue language passed to Colnect      |
| `--force`   | off                              | Overwrite an existing output file         |

The script runs Qt with the `offscreen` platform plugin (no display required)
and silences the importer's modal warning dialogs so a rate-limit or transient
error never blocks an unattended run.

After generating the file, review it (open it in OpenNumismat) and commit it.

> **Note:** the build cannot be run in environments where `colnect.com` is
> blocked by egress policy or where Colnect API keys are unavailable.
