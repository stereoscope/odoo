# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Odoo 19 (Community + Enterprise) ERP installation for Gaschler, a client project by Stereoscope. The repo is a fork of Odoo Community with enterprise and custom addons as git submodules.

- **Odoo version**: 19.0 (Python 3.10–3.13, PostgreSQL 13+)
- **Database**: `odoo_19` on localhost:5432, user `dba`
- **Config**: `odoo.conf`

## Database Credentials
psql via user fritz no password 
or look into odoo.conf

## Repository Structure

```
odoo-bin                    # Entry point: ./odoo-bin [command] [options]
odoo/                       # Core framework
  orm/                      #   ORM (models, fields, environments, registry)
  tools/                    #   Utilities (config, cache, SQL helpers, profiler)
  modules/                  #   Module loader/discovery
  tests/                    #   Test framework (base classes, tag system)
  addons/                   #   Core + enterprise addons (merged via symlinks)
    base/                   #   Base module (always installed)
addons/                     # Community addons (~100 modules)
libs/                       # Git submodules
  addons-enterprise/        #   Odoo Enterprise (submodule → odoo/enterprise)
  addons-dp/                #   Datenpol addons (submodule → datenpol/odoosh-gaschler)
    3rd-party-addons        #     Purchased third party addons
    custom-addons/          #     Odoo 19 custom modules (store, product_eprel, product_brand, product_pim_icecat, etc.)
```

The `odoo/addons/` directory contains both core and enterprise modules (enterprise modules are symlinked in via `cli.py link-addons`). Custom modules (stock_taking, store, product_eprel, product_brand, product_pim_icecat, etc.) live in `libs/addons-dp/custom-addons/`.

## Common Commands

### Running the Server
```bash
./odoo-bin                                    # Start server (default command)
./odoo-bin --addons-path=odoo/addons   # Explicit addons path
./odoo-bin -d odoo_19 -u module_name          # Update a specific module
./odoo-bin -d odoo_19 -i module_name          # Install a module
./odoo-bin shell -d odoo_19                   # Interactive Python shell
./odoo-bin --dev=xml,reload -d odoo_19         # Dev mode: live XML + auto-reload on code changes
```

`--dev` flags: `access` (log access errors), `qweb` (compiled XML in errors), `reload` (restart on changes), `replica` (simulate readonly replica), `werkzeug` (HTML debugger), `xml` (read views from source, not DB).

### Linking addons

Making sure all necessary addons are placed in the odoo/addons folder for easier navigation and simplicity

```bash
./libs/addons_custom/cli.py link-addons ./libs/addons-enterprise ./addons ./libs/addons-dp/custom-addons ./libs/addons-dp/3rd-party-addons ./libs/addons-dp/dp-apps ./libs/addons_custom/addons
```

### Running Tests
```bash
# Test a specific module
./odoo-bin --test-tags /module_name -d odoo_19 --stop-after-init

# Test a specific class
./odoo-bin --test-tags :TestClassName -d odoo_19 --stop-after-init

# Test a specific method
./odoo-bin --test-tags :TestClassName.test_method -d odoo_19 --stop-after-init

# Run post-install tests only
./odoo-bin --test-tags post_install -d odoo_19 --stop-after-init

# Exclude specific tags
./odoo-bin --test-tags=-slow_tests -d odoo_19 --stop-after-init

# Run a specific test file
./odoo-bin --test-file path/to/test_file.py -d odoo_19 --stop-after-init
```

Tests always require `-d <database>` and typically `--stop-after-init`. The `--test-enable` flag runs all tests for modules being installed/updated.

### Playwright E2E Tests (custom)
Browser-driven End-to-End tests for shop / portal / backend flows live in `libs/addons_custom/tests/e2e/`. They run against a **live** Odoo server (default `http://localhost:8069`, DB `odoo_19`) — completely outside the Odoo test runner.

```bash
# Run a single class with the venv pytest
cd libs/addons_custom
../../.venv/bin/pytest tests/e2e/test_website_shop.py::TestGuestCheckoutFullFlow -v

# Marker-based selection (markers registered in libs/addons_custom/pytest.ini)
../../.venv/bin/pytest tests/e2e -v -m full_checkout

# Visible browser (headed) — good for debugging
../../.venv/bin/pytest tests/e2e/... -v --headed --slowmo=300

# Built-in artifacts
../../.venv/bin/pytest tests/e2e/... --tracing=on --output=/tmp/trace
../../.venv/bin/playwright show-trace /tmp/trace/test_*/trace.zip
```

Fixtures (`tests/e2e/conftest.py`): `page` (admin-logged-in), `public_page` (guest), `db` (direct psycopg2). Override via env: `ODOO_URL`, `ODOO_DB`, `ODOO_LOGIN`, `ODOO_PASSWORD`.

**Shared base & helpers (`tests/e2e/_base.py`):** Test classes inherit `BaseE2ETest` to get `self._shot(label)` (auto step screenshots) and `self._dismiss_cookies()` (MutationObserver-based banner killer that survives navigations). Stateless helpers — `navigate_to_product_detail`, `navigate_to_shop_search`, `open_product_form`, `click_tab`, `open_action`, `get_schema_org_data` — are imported as module-level functions: `from _base import BaseE2ETest, open_action, click_tab`.

**Step screenshots (auto-on):** `self._shot("label")` drops numbered full-page PNGs to `tests/e2e/screenshots/<test_file_stem>/<test_name>/NN_<label>.png`. Stale shots are wiped at test start. Disable with `STEP_SCREENSHOTS=0`. The folder is `.gitignore`'d.

### Linting
Ruff is NOT installed in this environment. Follow Odoo coding conventions and PEP 8 manually. Do NOT attempt to run ruff.

### Other CLI Commands
```bash
./odoo-bin scaffold <name> <path>   # Generate module skeleton
./odoo-bin db --help                # Database operations (create, drop, dump, load)
./odoo-bin cloc -d odoo_19          # Count lines of code per module
./odoo-bin populate -d odoo_19      # Populate DB with test data
```

## Odoo Module Conventions

### Module Structure
```
module_name/
  __manifest__.py       # Module metadata (name, version, depends, data)
  __init__.py           # Python imports
  docs/                 # Contains Manual.md for module usage
  models/               # Business logic (ORM models)
  views/                # XML views, actions, menus
  security/             # ir.model.access.csv, record rules
  data/                 # Default data, demo data
  tests/                # Test files (must be imported in tests/__init__.py)
  static/               # Web assets (JS, CSS, images)
    description/
      icon.png          # Logo      
  wizard/               # Transient models for wizards
  report/               # QWeb report templates
```

## Manifest

```
  'author': 'Friedrich Gaschler',
  'website': 'http://www.gaschler.at',
  'license': 'Other proprietary',
```

Path to logo: ./libs/addons_custom/addons/static/description/icon.png

### Test Structure — MANDATORY for new modules
**When creating a new module, ALWAYS write tests.** Every new module must include a `tests/` directory with meaningful unit and integration tests covering the expected scenarios.

- Tests go in `module_name/tests/`, imported in `tests/__init__.py`
- Base class: `TransactionCase` (rollback per test) — do NOT use `AccountTestInvoicingCommon` or `TestAccountReportsCommon` as they create a second company which fails due to NOT NULL constraints from installed 3rd-party modules (`product_brand`)
- Default tags: `standard`, `at_install` — use `@tagged('post_install', '-at_install')` for post-install tests
- Tag format for `--test-tags`: `[-][tag][/module][:class][.method]`
- **Odoo 19**: `account.account` has no `company_id` field (multi-company by default) — don't pass it in test data
- Always run tests after creating them: `.venv/bin/python odoo-bin --test-tags /module_name -d odoo_19 --stop-after-init --http-port=8099`
- Tests must cover: happy path, edge cases, configuration toggles, and access control where relevant
- **UI-Tests (HttpCase/Tours)**: Erwägen bei Wizards mit mehreren Schritten, komplexen Form-Interaktionen (Onchange-Ketten, dynamische Sichtbarkeit), POS-Frontend-Logik oder Website-Flows. Nicht nötig für einfache Felder, Standard-Reports oder reine Backend-Logik ohne eigene UI.

### ORM Key Points
- In Odoo 17+, translatable `Char`/`Text` fields are stored as `jsonb` (e.g., `{"en_US": "value"}`). Company-dependent fields also use jsonb.
- `read_group()` is deprecated since 19.0 — use `_read_group()` instead
- For bulk inserts (10K+ records), raw SQL with `INSERT...SELECT` avoids ORM cache OOM — call `self.env.invalidate_all()` after
- **Never guess Odoo field names** — always verify by checking the model source (`grep` for the field definition in the relevant model file under `odoo/addons/` or `addons/`). Field names are often non-obvious (e.g., `group_ids` not `groups_id`, `categ_id` not `category_id`, `company_ids` not `companies`).
- Import order enforced by ruff: `future → stdlib → third-party → odoo → odoo.addons`

## Coding Style

- Follow Odoo coding guidelines and PEP 8
- Ruff is NOT installed — follow conventions manually
- Line length is NOT enforced (E501 ignored)
- `printf`-style string formatting is allowed (UP031 ignored)
- Unused imports in `__init__.py` are allowed (F401 ignored)

## Odoo LSP

Odoo provides a Language Server Protocol (LSP) implementation for IDE integration. It provides autocompletion, go-to-definition, and diagnostics for Odoo Python code (model fields, XML IDs, view inheritance).

- **Repository**: Part of the Odoo IDE tools / VS Code extension
- **Setup**: Configure via VS Code Odoo extension or standalone LSP pointing to the Odoo source and addons paths
- **Useful for**: Field name resolution, XML ID validation, model inheritance chains

# Additional Information

More information about ideas, concepts and todos can be found in the Obsidian vault at: /home/fritz/Syncthing/Obsidian_Vault/Odoo/

## Memory & Performance Limits (odoo.conf)

Configured for large imports (Icecat taxonomy):
- Hard memory limit: 3 GB / Soft memory limit: 2.5 GB
- CPU time limit: 3600s / Real time limit: 3600s

# Additional Code Repositories

- Android App for stock_taking can be found at /home/fritz/Documents/Projekte/Gaschler/MobileOdooApp
- **Price Crawler Odoo-Modul**: `/home/fritz/Documents/Projekte/Odoo/odoo_19/libs/addons_custom/addons/product_price_crawler/`
  - Vollständiges Odoo 19 CE Custom-Modul für AI-gestütztes Price Crawling (Geizhals.at)
  - Architektur-Plan & Memory: `/home/fritz/.claude/projects/-home-fritz-Documents-Projekte-Gaschler-gaschler-price-crawler/memory/MEMORY.md`
  - Docker-Setup: `/home/fritz/Documents/Projekte/Odoo/odoo_19/libs/addons_custom/addons/product_price_crawler/docker-compose.crawler.yml`
  - Alter Spring-Boot-Crawler (wird ersetzt) liegt hier: `/home/fritz/Documents/Projekte/Gaschler/gaschler-price-crawler`
- **Stundenaufzeichnung (Activity Report)**: `/home/fritz/Documents/Projekte/Odoo/odoo_19/libs/addons_custom/addons/gaschler_activity_report/`
  - Portiert von Java-Projekt (`/home/fritz/Documents/Projekte/Gaschler/gaschler-activity-report/`) nach Odoo 19 Modul `gaschler_activity_report`