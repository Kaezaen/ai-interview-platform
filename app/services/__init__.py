"""Business logic, transactions, and AI orchestration.

Services know nothing about HTTP objects and raise domain exceptions rather than
``HTTPException``; a central handler maps those to responses.
"""
