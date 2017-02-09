***********************
Contributing guidelines
***********************

- `PEP 8`_, when sensible.
- Write tests and docs for new features.
- Please update AUTHORS.rst when you contribute.
- Max line is set to 100 characters.
- Tests are not linted, but don't be terrible.

.. _`PEP 8`: http://www.python.org/dev/peps/pep-0008/


Imports should be ordered in pep8 style but ordered by line length.

.. code-block:: python

   # Good!
   import json
   import asyncio
   import unittest

   import pytest
   from furl import furl

   import aiohttpretty

   # Bad
   import pytest
   import aiohttpretty
   import unittest
   import asyncio
   import json


``aiohttpretty`` expects pretty pull requests, `clean commit histories`_, and meaningful commit messages.

- Make sure to rebase (``git rebase -i <commitsha>``) to remove pointless commits. Pointless commits include but are not limited to:

  - Fix flake errors
  - Fix typo
  - Fix test

- Follow the guidelines for commit messages in the above

  - Don't worry about new lines between bullet points

.. _`clean commit histories`: http://justinhileman.info/article/changing-history/


``aiohttpretty`` uses `semantic versioning`_ ``<major>.<minor>.<patch>``

- Patches are reserved for hotfixes only
- Minor versions are for **adding** new functionality or fields
- Minor versions **will not** contain breaking changes to the existing API

  - Any changes **must** be backwards compatible

- Major versions **may** contain breaking changes to the existing API

.. _`semantic versioning`: http://semver.org/
