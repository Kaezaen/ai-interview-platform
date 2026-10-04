"""Test suite.

A package rather than a bare directory so that pytest imports conftest as
``tests.conftest`` — the same module the test files import their helpers
from. Without it, conftest would be imported twice under two names, and its
module-level database-URL rewrite would run twice.
"""
