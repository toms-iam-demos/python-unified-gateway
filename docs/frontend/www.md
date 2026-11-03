# PUG website component

Canonical implementation: `www/` in this repository. Design governance remains ADR-0011 and the existing frontend specifications. This component supplies the reusable website shell and profile boundary; it does not replace those specifications or claim completion of the full workbench.

The website owns homepage presentation, navigation, catalog metadata, example landing templates and shared static assets. An external deployment profile owns approved organization-specific content and asset references. Connected demo backends, execution state, recordings and secured artifacts retain separate ownership.

Navigation and catalog entries derive from Python registries and validated profile data. Dropdowns float outside document flow at desktop/tablet sizes; narrow screens use an overlay menu. Site copy and titles contain no em dashes.

The current hosted prototype predates this package. Adding repository source is not a declaration that the live image has been rebuilt from it. Replacing that prototype requires a reviewed profile migration and explicit deployment, with the existing routes and evidence preserved.

See [website implementation and deployment instructions](../../www/README.md).
