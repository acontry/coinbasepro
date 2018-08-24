.. :changelog:

Release History
---------------

dev
+++

- [Short description of non-trivial change.]

0.0.6 (2018-08-23)
++++++++++++++++++

**Improvements**

- Update parameter validation for `get_fills` to reflect Coinbase API change.

**Bugfixes**

- Fixed bug where parameters had no effect in `get_product_historic_rates`.
- Fixed bug where `product_id` parameter had no effect in `cancel_all`.

0.0.5 (2018-08-21)
++++++++++++++++++

**Improvements**

- Add exceptions for Coinbase error responses.

0.0.4 (2018-07-15)
++++++++++++++++++

**Improvements**

- Updated stop orders to latest API.

**Bugfixes**

- Fix issue with time in force error checking.

0.0.3 (2018-07-07)
++++++++++++++++++

**Improvements**

- Rename deposit and withdraw methods to clarify action.

**Bugfixes**

- Removed margin endpoints - now unsupported.

0.0.2 (2018-07-01)
+++++++++++++++++++

**Improvements**

- Client request timeout is now configurable.

0.0.1 (2018-06-27)
+++++++++++++++++++

- Hello world.