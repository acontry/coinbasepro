.. :changelog:

Release History
---------------

dev
+++

- [change here]

0.2.1 (2020-01-09)
++++++++++++++++++

**Bugfixes**

- Fix volume parsing error in `get_fills`.

0.2.0 (2019-11-10)
++++++++++++++++++

**Improvements**

- Added rate-limiting to all public and authenticated endpoints. Dropping support for Python 3.4 to keep the implementation simple.

0.1.1 (2019-07-23)
++++++++++++++++++

**Bugfixes**

- Parameters used for historic rates (start/end) were not being sent in query parameters (thanks imalovitsa-exos!).

0.1.0 (2019-03-20)
++++++++++++++++++

**Improvements**

- Return values are now Pythonic types (i.e Decimal, datetime) instead of all string types.
- Python3 typing now used to help with development using this API.
- Docstring improvements and changes to match updated interface.
- A bit more documentation in the readme.

**Bugfixes**

- Update requests version to >=2.20.0 to address security vulnerability.

0.0.7 (2018-09-09)
++++++++++++++++++

**Bugfixes**

- Fix parameter name for `get_product_historic_rates`.

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
