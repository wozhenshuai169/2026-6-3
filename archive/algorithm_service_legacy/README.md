# Legacy Algorithm Service Archive

This directory was moved from the repository root on 2026-07-13. It is not
imported by `app.main`, is not a product deployment target, and must not receive
new product features.

The active algorithm implementation is `src/ai_algorithm_service/`, invoked by
`app/services/algorithm_facade.py` from the authenticated `/api/...` backend
flow. This archive is retained only for historical comparison while the team
finishes migration documentation.
