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
  addons_custom/            #   Custom addons (submodule → stereoscope/odoo_addons)
    addons/nineteen/        #     Odoo 19 custom modules (gaschler_core, product_pim_icecat, etc.)
  addons-dp/                #   Datenpol addons (submodule → datenpol/odoosh-gaschler)
```

The `odoo/addons/` directory contains both core and enterprise modules (enterprise modules are symlinked in). Custom modules live in `libs/addons_custom/addons/nineteen/`.

## Common Commands

### Running the Server
```bash
./odoo-bin                                    # Start server (default command)
./odoo-bin --addons-path=addons,odoo/addons   # Explicit addons path
./odoo-bin -d odoo_19 -u module_name          # Update a specific module
./odoo-bin -d odoo_19 -i module_name          # Install a module
./odoo-bin shell -d odoo_19                   # Interactive Python shell
./odoo-bin --dev=xml,reload -d odoo_19         # Dev mode: live XML + auto-reload on code changes
```

`--dev` flags: `access` (log access errors), `qweb` (compiled XML in errors), `reload` (restart on changes), `replica` (simulate readonly replica), `werkzeug` (HTML debugger), `xml` (read views from source, not DB).

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

### Linting
```bash
ruff check .                  # Lint (config in ruff.toml)
ruff check --fix .            # Lint with auto-fix
```

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

### Test Structure
- Tests go in `module_name/tests/`, imported in `tests/__init__.py`
- Base classes: `TransactionCase` (rollback per test), `SingleTransactionCase`, `HttpCase` (browser)
- Default tags: `standard`, `at_install` — use `@tagged('post_install', '-at_install')` for post-install tests
- Tag format for `--test-tags`: `[-][tag][/module][:class][.method]`

### ORM Key Points
- In Odoo 17+, translatable `Char`/`Text` fields are stored as `jsonb` (e.g., `{"en_US": "value"}`). Company-dependent fields also use jsonb.
- `read_group()` is deprecated since 19.0 — use `_read_group()` instead
- For bulk inserts (10K+ records), raw SQL with `INSERT...SELECT` avoids ORM cache OOM — call `self.env.invalidate_all()` after
- Import order enforced by ruff: `future → stdlib → third-party → odoo → odoo.addons`

## Coding Style

- Follow Odoo coding guidelines and PEP 8
- Ruff is configured with extensive rules in `ruff.toml` (target: Python 3.10)
- Line length is NOT enforced (E501 ignored)
- `printf`-style string formatting is allowed (UP031 ignored)
- Unused imports in `__init__.py` are allowed (F401 ignored)

# Additional Information

More information about ideas, concepts and todos can be found in the Obsidian vault at: /home/fritz/Syncthing/Obsidian_Vault/Odoo/

## Memory & Performance Limits (odoo.conf)

Configured for large imports (Icecat taxonomy):
- Hard memory limit: 3 GB / Soft memory limit: 2.5 GB
- CPU time limit: 3600s / Real time limit: 3600s

# Additional Code Repositories

- Android App for stock_taking can be found at /home/fritz/Documents/Projekte/Gaschler/MobileOdooApp