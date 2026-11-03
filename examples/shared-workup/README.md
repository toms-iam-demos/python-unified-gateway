# Illustrated demo workups

Every demo example needs an inspectable workup alongside its presentation. This dependency-free renderer provides the shared structure for workflow illustrations, evidence, system responsibilities and remaining acceptance gates.

## Required content

Supply a title, summary, explicit status and evidence basis. Each workup contains at least one ordered workflow with descriptions for every step, optional decision branches and a stated outcome. Evidence records require a source and an explicit state. System descriptions must identify their boundaries. Acceptance gates remain visible even when the main path is complete.

Supported evidence states are `native`, `fixture`, `design`, `retained` and `implemented`. A label must state what was actually established. A retained specification is not a successful run. One example's receipt must not be used as another example's acceptance evidence. Reconstructed diagrams must not be described as screenshots or live provider monitors.

Use `assertCoverage(entries, workups)` in the publication build. It fails for a missing workup, duplicate entry or incomplete content. Add a tailored workup whenever adding a catalog example. Do not replace it with a generic placeholder or borrow a verified badge from a related scenario.

## Integration

Load `workup-renderer.js` and `workup.css`. The browser API is `window.PUGWorkup`; Node can require the same file for static generation and build validation.

```javascript
PUGWorkup.assertCoverage(entries, workups);
host.innerHTML = PUGWorkup.render(workups[exampleId]);
```

The full view uses `#workup` and chapter anchors. Pass `{id: 'workflow-proof', workflowOnly: true}` to embed just the illustrated narrative inside an existing detailed workup. Each workflow also receives a numbered deep-link anchor. An embedding single-page application must recognize these anchors before rendering or scrolling.

The renderer escapes all supplied text, accepts no raw HTML or external resource URLs and performs no network calls. Do not include credentials, personal records, provider identifiers or private source links in content intended for sharing. Keep institution-specific data outside this public component in accordance with the public identity policy.

## Verification

Run `node --test examples/shared-workup/test-workup.cjs`. The tests cover missing workups, explicit evidence and boundary requirements, incomplete acceptance records and HTML injection. Also validate the deployment's actual catalog data with `assertCoverage` and inspect desktop and phone layouts. Keep workflow headers in normal document flow so they cannot overlap text or page navigation.

This module describes work. Rendering it does not execute a workflow, establish provider acceptance or change a visitor's access scope.
