"""AI provider abstraction.

Provider SDKs may only be imported inside their own ``<provider>_provider`` module,
so business logic depends on the ``AIProvider`` interface and never on a vendor SDK.
"""
