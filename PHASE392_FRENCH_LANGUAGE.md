# Phase 392 — French Language Expansion

French is now a first-class language for the client surface:

- UI language registry: `ar`, `de`, `en`, `fr`.
- Language normalization accepts `fr`, `French`, `Français`, `francais`, and Arabic French labels.
- French is LTR and participates in the same central translation API used by existing languages.
- UI language, print language, and report language settings expose French.
- Browser HTML printing and emergency print-template fallback include French labels.
- Reports inherit the central report/print language setting and translation table.
- The French dictionary is generated after all phase-level Arabic/German/English translation updates so it covers late-added keys as well.

Quality gates:

- `tools/phase392_french_language_guard.py`
- `tests/test_phase392_french_language.py`
- `alrajhi_client/workspace/quality/french_language_contract.py`
