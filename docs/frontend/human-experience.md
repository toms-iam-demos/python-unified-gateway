# Human experience and developer identity

Accepted by the maintainer on 2026-11-03. Applies throughout the shared homepage, catalog, workspaces, example pages, workups and visitor screens under ADR-0011.

Use the docusign Developer Center as the visual reference for the developer shell: approved marks, locally available licensed typography, a clear page hierarchy, deliberate spacing and recognizable navigation. Do not copy a vendor's layout where it makes a business task harder. Technical reference pages may use compact structured data; committee presentations and operational stories lead with the decision, owner, evidence and next action. Keep organization identity in its approved profile. Preserve native screenshots and exports as evidence.

The design contract is:

- Body and decision text are comfortably readable, normally 16px or larger at the default browser setting. Supporting labels normally use 13px or more. Avoid very small all-cap paragraphs and long lines. Native captured diagrams are an exception only with zoom and an adjacent readable explanation.
- Pair foreground and surface colors explicitly. Meet the applicable WCAG 2.2 AA contrast criteria; do not rely on inheritance from dark navigation. Use text and shape as well as color to communicate status.
- Make controls comfortable to operate, normally at least 44 CSS pixels high. Respect the WCAG exceptions for inline links and complex diagrams while providing a usable text or keyboard alternative.
- All navigation and actions work with a keyboard. Focus is visible on light and dark surfaces. Menus support Escape, section links place focus on the destination, and sticky navigation does not cover that destination.
- Use native elements, meaningful names, proper labels and a coherent heading outline. Loading, error, empty and success states explain what happened and what the person can do next. A generated or simulated result is never styled as native completion evidence.
- Preserve readable content at 320 CSS pixels and browser enlargement. Tables and diagrams may scroll within a named region when two-dimensional layout is necessary. Ordinary paragraphs and controls must reflow. Honor reduced motion and forced colors.
- Keep useful detail available through progressive disclosure. Do not place internal implementation commentary in a visitor's task flow unless it helps their decision. Keep the complete workup and provenance available.
- Security boundaries remain server-enforced. Readable disabled menu items do not acquire links. Accessibility improvements do not extend sessions, weaken authentication, authorize provider operations or change an invitation's scope.

The engineering target is WCAG 2.2 AA. It is not a claim of ADA compliance or a conformance certification. Docusign's [accessibility hub](https://www.docusign.com/accessibility) describes its own ongoing accessibility program and product-specific reports. Those reports do not certify PUG or every Developer Center page. Use the [WCAG 2.2 reference](https://www.w3.org/WAI/WCAG22/quickref/) for the criteria applicable to the actual implementation.

For each shared presentation release, record the routes and viewports checked, keyboard tasks exercised, contrast observations, form/heading semantics, source revision and deployed artifact hashes. Automated checks do not replace task testing with a screen reader and disabled users. Record remaining gaps honestly. Do not turn a passing visual review into a claim that all criteria or all native workflow branches passed.

The implementation baseline is [shared UI support](../../examples/shared-ui/README.md) plus the [illustrated workup component](../../examples/shared-workup/README.md). Extend these shared components before adding page-specific exceptions.
