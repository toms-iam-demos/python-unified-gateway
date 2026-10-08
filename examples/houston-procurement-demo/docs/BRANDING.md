# Houston employee procurement workspace: design provenance

Updated 2026-10-07. This is an independent PUG demonstration using Houston's public visual identity. It is not an observed, authenticated city intranet, an official service or a city-endorsed application. No login credentials are requested or collected.

## What comes from Houston

| Element | Source | Treatment |
| --- | --- | --- |
| City seal | [Official masthead asset](https://houstontx.gov/_siteAssets/images/citySeal125x125.png), referenced by the [SPD homepage](https://www.houstontx.gov/bizwithhou/) | Use the actual image, preserve proportions and colors, provide an explicit demonstration alt label. Do not redraw the seal or invent a municipal mark. |
| Buffalo Bayou / skyline banner | [Official page's Rosemont photograph](https://houstontx.gov/2023upgrade/images/rosemont-day.jpg) | Use the same scenic context with a dark gradient so operational copy remains legible. The public page itself references this image in its banner style. |
| Fjalla One and Open Sans | [City main stylesheet](https://houstontx.gov/_siteAssets/css/main.css) | Use Fjalla One for department/display headings and Open Sans for body text and controls. Fonts are bundled locally, with their SIL Open Font License files. |
| Departmental blue | [Published 2023 light stylesheet](https://houstontx.gov/2023upgrade/css/2023-light.css) and SPD page styles | Adapt the observed `#34587F` color for navigation and primary actions. These are observed website values, not a claim that a formal city brand manual mandates them. |
| Department naming and procurement resources | [Strategic Procurement Division homepage](https://www.houstontx.gov/bizwithhou/) | Retain the department name and provide links to actual public policy, supplier, Beacon, HoustonBuy and OBO resources. Links are clearly external. |

## What is our design

The public site is designed for residents and suppliers. An employee workspace needs a different hierarchy: department context first, the user's review queue next, and policies within reach. The new sidebar, reviewer persona, four task entries, metrics, decision trail and integration lab are proposed interface elements. They are not claims about Houston's real internal portal.

The masthead leads with the city identity; PUG and docusign appear as the workflow layer. This makes the demo feel like a procurement team's everyday workspace instead of a vendor landing page. The skyline is restrained to the welcome panel so evidence and actions retain visual priority. Blue is used for normal operations, amber for attention, and red for blockers or cleanup. Color is supplemented with written status labels.

“Contract reviewer” is explicitly a **demo persona**, not an authenticated user. The narrow environment ribbon stays visible at the top. This permits an immersive post-login-style concept without a fake authentication screen or misleading claim that city access has been granted.

## Assets and rights

- The seal and photograph are third-party City of Houston website assets; their source locations are credited above. This project makes no claim of ownership, trademark permission, endorsement or an open-content license for those assets. City asset rights remain with their respective owners; assess reuse separately for an external production service.
- The fonts are obtained through Google Fonts. License copies: `app/static/brand/fjallaone-OFL.txt` and `app/static/brand/opensans-OFL.txt`. Upstream: [Fjalla One](https://github.com/google/fonts/tree/main/ofl/fjallaone), [Open Sans](https://github.com/google/fonts/tree/main/ofl/opensans).
- Application styles are newly authored adaptations; the city's entire CSS framework, analytics, accessibility scripts, contact forms and live solicitation widget are not copied into the application.
- Assets are served locally to preserve portability and avoid runtime font/image requests to city or Google servers. This does not change the separate externally hosted Swagger UI asset behavior documented in the technical report.
