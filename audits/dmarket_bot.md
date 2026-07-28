# Audit: Cfomodz/dmarket_bot

**Date:** 2026-07-28
**Status:** Audited (agentic deep-read; 93 unit tests pass; key findings verified at runtime)

## Summary

Asyncio trading bot for the DMarket skin marketplace (Rust by default; CS2/
Dota2/TF2 supported): crawls market items into a local SQLite (peewee) price
history DB, filters through profitability heuristics, then continuously
places/adjusts buy orders via DMarket's Ed25519-signed REST API. Sell/reprice
loops exist but are disabled. No API keys committed (single squashed commit;
credentials from `.env`).

## Findings

### 1. `check_offers` crashes with TypeError — the default buy loop never places an order — critical

`modules/orders.py:290-293`: `offer_prices = [o.price.USD for o in offers]`
keeps raw values, then `any(my_sell_price <= p ...)` compares float to `str`
(pydantic v2 smart-union preserves the API's string values; line 290 itself
sorts with `int(...)`, confirming). Verified at runtime: `TypeError`. Every
cycle raises, is swallowed by `main.py:44`, retries forever — the bot buys
nothing. Fix: `my_sell_price <= int(p)`.

### 2. Division by zero when an item has no buy targets — critical

`modules/orders.py:179-180`: empty `Targets` list → `best_target = 0` →
`ZeroDivisionError` (verified). With default `FREQUENCY = True` all skins pass
through here, so one target-less item aborts the whole order-update cycle.
Related: line 172 averages raw dollars while the rest of the file uses cents
(`sale_price_amount()`), skewing `profit_by_avg`. Skip `best_target == 0`; use
`sale_price_amount` consistently.

### 3. `zip(skins, aggregated)` misaligns prices when the API omits a title — warning

`modules/orders.py:112,133`: both lists are sorted and zipped, but
`aggregated_prices` returns only titles that have aggregates — one missing
title shifts every subsequent pairing, so skin "A" gets skin "B"'s
`orderBestPrice` and buy orders are created at another item's price. Direct
money risk. Build a title-keyed dict as `modules/offers.py:144` already does.

### 4. `update_offers` is a silent no-op: `select_not_sell` drops `OfferID` — warning

`db/crud.py:135` rebuilds `SellOffer` with only `AssetID`/`buyPrice`,
discarding `OfferID`/`title`/`fee`; `modules/offers.py:136-137` filters
`if i.OfferID` — always `None` — so the advertised dynamic repricing never
executes. Fix: `SellOffer.model_validate(s)` (model already has
`from_attributes=True`).

### 5. `.env.example` referenced everywhere but not committed — warning

`README.md:21` says `cp .env.example .env`, `config.py:16-17` raises an error
pointing at it, `.gitignore:17` carves out `!.env.example` — the file doesn't
exist. Quick-setup fails at step 4. Commit one with placeholder keys.

### 6. README advertises features the default config doesn't run — info

`README.md:41-44` claims auto-listing with dynamic repricing and all-games
support, but `main.py:101-105` has the sell/reprice loops commented out and
`config.py:30` defaults to Rust only. Enable the loops (after fixing 2 and 4)
or document what actually runs.

### 7. `boost_control` mutates the list it's indexing — warning

`modules/orders.py:93-98`: iterates indices of a precomputed moving-average
list while `item.sales.pop(i)` shifts the data; subsequent comparisons test
mismatched pairs, possibly deleting the wrong sales; the eventual `IndexError`
is swallowed (lines 101-102). Collect indices first, then rebuild.

### 8. No LICENSE file — info

Public repo with sponsor badges but no license — legally all-rights-reserved.
Add one (e.g. MIT) plus license metadata in `pyproject.toml`.

## TODOs

- [ ] Cast offer prices to `int` in `check_offers` (modules/orders.py:293)
- [ ] Guard `best_target == 0`; use `sale_price_amount` for the average (modules/orders.py:172-180)
- [ ] Replace `zip(skins, aggregated)` with title-keyed dict (modules/orders.py:112,133)
- [ ] Return fully-populated `SellOffer` from `select_not_sell` (db/crud.py:135)
- [ ] Commit `.env.example` with placeholder `DMARKET_PUBLIC_KEY`/`DMARKET_SECRET_KEY`
- [ ] Document (or re-enable) the disabled sell loops in README
- [ ] Rewrite `boost_control` to avoid mutating while iterating (modules/orders.py:93-98)
- [ ] Add LICENSE + `pyproject.toml` license metadata
