// Native browser readiness only. The worker key and provider authorization remain mandatory.
export function hasWorkflowSession({expectedURL, actualURL, title, newWorkflowVisible, loginPromptVisible}) {
  try {
    const expected = new URL(expectedURL), actual = new URL(actualURL);
    return expected.protocol === 'https:' && actual.origin === expected.origin &&
      actual.pathname === expected.pathname && Boolean(expected.searchParams.get('aid')) && expected.searchParams.getAll('aid').length === 1 &&
      actual.searchParams.getAll('aid').length === 1 &&
      actual.searchParams.get('aid') === expected.searchParams.get('aid') &&
      title === 'Workflows - Docusign CLM' && newWorkflowVisible === true &&
      loginPromptVisible === false;
  } catch { return false; }
}
