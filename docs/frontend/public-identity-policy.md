# Public identity policy

Effective 2026-10-09. Applies to the current tracked publication tree. Git history, old branches, previous pull requests, forks, caches and downloaded copies are explicitly outside this cleanup. The maintainer requested no history rewrite.

Use NFP (not-for-profit), Museum, Municipal and EDU as organization types. Use synthetic people, suppliers, IDs and scenario assumptions. Technical product names and required software/font attribution remain accurate. Repository ownership is not a represented demo organization.

Review names and indirect identifiers in paths, URLs, agency acronyms, source references, captions, notifications, configuration keys, fixtures, diagrams, screenshots, binary metadata and embedded source. Remove identifying assets or replace them with original generic artwork. Do not invent a generic source URL or turn a real institutional policy into an unattributed fact. Explicitly label fixture assumptions.

`python tools/check_public_identity.py` scans current Git-tracked filenames and decoded content for known identifying terms using normalization and fingerprints. Fingerprints keep the removed names out of the checker itself; they are not cryptographic anonymization. It reads font name metadata using its actual encoding, rejects unsupported binary content for review, and rejects PlantUML embedded source comments. Tests exercise filename/content matches, encoded text and vendor-name tolerance. CI runs this on every push and pull request.

This is a regression guard, not proof of full anonymity: unknown names, visual resemblance, arbitrary binary formats, OCR and historical material require human review. Font license metadata is retained. Newly added images and captures require visual and provenance review before publication. No secrets, tokens or real personal records should be included regardless of this check.
