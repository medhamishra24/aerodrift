const state = {
  scan: null,
  topology: null,
  history: null,
};

const byId = (id) => document.getElementById(id);

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>'"]/g, (character) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    "'": '&#039;',
    '"': '&quot;',
  }[character]));
}

function formatTimestamp(value) {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString([], {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', hour12: false,
  });
}

function setFeedback(message, type = 'loading') {
  const feedback = byId('feedback');
  feedback.className = `feedback ${type}`;
  feedback.innerHTML = type === 'loading'
    ? `<span class="loader" aria-hidden="true"></span><span>${escapeHtml(message)}</span>`
    : `<span>${escapeHtml(message)}</span>`;
}

async function getJson(path) {
  const response = await fetch(path, { headers: { Accept: 'application/json' } });
  if (!response.ok) throw new Error(`${path} returned HTTP ${response.status}`);
  return response.json();
}

function renderOverview(scan) {
  const topology = scan.topology || {};
  const drift = scan.drift || {};
  byId('node-count').textContent = topology.node_count ?? '—';
  byId('edge-count').textContent = topology.edge_count ?? '—';
  byId('drift-status').textContent = drift.status || '—';
  byId('drift-status').style.color = drift.status === 'NO DRIFT' ? 'var(--green)' : 'var(--red)';
  byId('drift-note').textContent = drift.internet_to_database_path ? 'Internet can reach database' : 'No unsafe route detected';
  byId('risk-level').textContent = drift.risk_level || '—';
  byId('risk-level').style.color = drift.risk_level === 'SAFE' ? 'var(--green)' : 'var(--amber)';
  byId('affected-count').textContent = (drift.affected_resources || []).length;
  byId('scan-time').textContent = formatTimestamp(scan.timestamp);
  byId('last-updated').textContent = `Last service response · ${formatTimestamp(scan.timestamp)} UTC`;
}

function renderDrift(scan) {
  const drift = scan.drift || {};
  const unsafe = Boolean(drift.internet_to_database_path);
  const panel = byId('drift-panel');
  const exposure = document.querySelector('.exposure-state');
  const badge = byId('severity-badge');
  panel.classList.toggle('safe-panel', !unsafe);
  exposure.classList.toggle('safe', !unsafe);
  badge.className = `severity-badge ${unsafe ? 'danger' : 'safe'}`;
  badge.textContent = unsafe ? 'HIGH RISK' : 'SAFE';
  byId('exposure-icon').textContent = unsafe ? '!' : '✓';
  byId('exposure-status').textContent = unsafe ? 'DRIFT DETECTED' : 'NO DRIFT';
  byId('exposure-message').textContent = drift.message || 'No finding message available.';
  byId('reachability').textContent = unsafe ? 'Internet → Database: YES' : 'Internet → Database: NO';
  byId('security-group').textContent = drift.security_group?.id || 'None identified';
  byId('unsafe-cidr').textContent = drift.security_group?.rule || 'None identified';
  const path = drift.path || [];
  byId('path-count').textContent = `${path.length} ${path.length === 1 ? 'hop' : 'hops'}`;
  byId('path-flow').innerHTML = path.length
    ? path.map((resourceId, index) => {
      const resource = (drift.affected_resources || []).find((item) => item.id === resourceId);
      const name = resource?.name || resourceId;
      return `<div class="path-node"><span class="node-index">${index + 1}</span><span class="path-node-name">${escapeHtml(name)}<span class="path-node-id">${escapeHtml(resourceId)}</span></span></div>${index < path.length - 1 ? '<span class="path-arrow" aria-hidden="true">→</span>' : ''}`;
    }).join('')
    : '<span class="empty-state">No Internet-to-Database path detected.</span>';
  const recommendations = drift.recommendations || [];
  byId('recommendations').innerHTML = recommendations.length
    ? recommendations.map((recommendation) => `<li>${escapeHtml(recommendation)}</li>`).join('')
    : '<li>No recommendations returned.</li>';
}

function renderTopology(topology) {
  state.topology = topology;
  byId('snapshot-id').textContent = `Snapshot ${topology.snapshot_id || '—'}`;
  const path = state.scan?.drift?.path || [];
  const pathEdges = new Set(path.slice(0, -1).map((source, index) => `${source}->${path[index + 1]}`));
  byId('topology-map').innerHTML = (topology.edges || []).length
    ? topology.edges.map((edge) => {
      const unsafe = pathEdges.has(`${edge.source}->${edge.target}`);
      const source = (topology.nodes || []).find((node) => node.id === edge.source);
      const target = (topology.nodes || []).find((node) => node.id === edge.target);
      return `<div class="edge-row ${unsafe ? 'unsafe' : ''}"><div class="edge-node ${unsafe ? 'unsafe-node' : ''}"><strong>${escapeHtml(source?.name || edge.source)}</strong><span>${escapeHtml(edge.source)}</span></div><div class="edge-connector" aria-label="directed to">→</div><div class="edge-node ${unsafe ? 'unsafe-node' : ''}"><strong>${escapeHtml(target?.name || edge.target)}</strong><span>${escapeHtml(edge.target)}</span></div><div class="edge-label">${escapeHtml(edge.relationship || 'connected to')}${unsafe ? ' · unsafe path' : ''}</div></div>`;
    }).join('')
    : '<span class="empty-state">No topology edges returned.</span>';
  byId('node-list').innerHTML = (topology.nodes || []).length
    ? topology.nodes.map((node, index) => `<div class="inventory-node"><span class="inventory-node-mark">${String(index + 1).padStart(2, '0')}</span><span><strong>${escapeHtml(node.name || node.id)}</strong><span>${escapeHtml(node.resource_type || 'Resource')} · ${escapeHtml(node.id)}</span></span></div>`).join('')
    : '<span class="empty-state">No topology nodes returned.</span>';
}

function renderHistory(history) {
  state.history = history;
  const changed = history.status === 'CHANGES DETECTED';
  const badge = byId('history-status');
  badge.className = `history-badge ${changed ? '' : 'safe'}`;
  badge.textContent = history.status || 'UNKNOWN';
  const added = history.added_nodes || [];
  const removed = history.removed_nodes || [];
  byId('added-count').textContent = added.length;
  byId('removed-count').textContent = removed.length;
  byId('added-list').innerHTML = added.length ? added.map((node) => `<li>+ ${escapeHtml(node.name || node.id)}</li>`).join('') : '<li>None</li>';
  byId('removed-list').innerHTML = removed.length ? removed.map((node) => `<li>− ${escapeHtml(node.name || node.id)}</li>`).join('') : '<li>None</li>';
  const edgeChanges = [...(history.added_edges || []).map((edge) => `+ ${edge.source} → ${edge.target}`), ...(history.removed_edges || []).map((edge) => `− ${edge.source} → ${edge.target}`)];
  byId('edge-diff').textContent = edgeChanges.length ? edgeChanges.join(' · ') : 'No topology edge changes reported.';
}

function renderRemediation(scan) {
  const remediation = scan.remediation;
  const badge = byId('remediation-badge');
  const icon = byId('remediation-icon');

  if (!remediation) {
    badge.className = 'remediation-badge';
    badge.textContent = 'NOT REQUIRED';
    icon.textContent = '—';

    byId('remediation-status').textContent = 'No remediation required';
    byId('remediation-message').textContent =
      'No unsafe drift was detected in the latest scan.';

    byId('remediation-sg').textContent = '—';
    byId('remediation-operation').textContent = '—';
    byId('remediation-protocol').textContent = '—';
    byId('remediation-port').textContent = '—';
    byId('remediation-cidr').textContent = '—';
    byId('remediation-safety').textContent = '—';
    byId('remediation-lifecycle').textContent = '—';
    byId('remediation-code').textContent =
      'No remediation code generated.';
    byId('remediation-attempt').textContent = '—';
    byId('remediation-execution-time').textContent = '—';
    return;
  }

  const audit = remediation.audit || {};
  const metadata = audit.action_metadata || {};

  const success = Boolean(remediation.success);

  badge.className = `remediation-badge ${success ? 'success' : 'failed'}`;
  badge.textContent = success ? 'SUCCESS' : 'FAILED';

  icon.textContent = success ? '✓' : '!';

  byId('remediation-status').textContent =
    success ? 'Remediation completed' : 'Remediation requires review';

  byId('remediation-message').textContent =
    remediation.message || remediation.details || 'No remediation message available.';

  byId('remediation-sg').textContent =
    audit.security_group_id || '—';

  byId('remediation-operation').textContent =
    remediation.operation || 'Revoke ingress';

  byId('remediation-protocol').textContent =
    metadata.protocol || '—';

  byId('remediation-port').textContent =
    metadata.from_port != null
      ? `${metadata.from_port} → ${metadata.to_port}`
      : '—';

  byId('remediation-cidr').textContent =
    metadata.source_cidr || '—';

  byId('remediation-safety').textContent =
    audit.safety_decision || '—';

  byId('remediation-lifecycle').textContent =
    audit.lifecycle_stage || '—';

  byId('remediation-code').textContent =
    remediation.generated_action || 'No generated code available.';

  byId('remediation-attempt').textContent =
    audit.attempt_id || '—';

  byId('remediation-execution-time').textContent =
    formatTimestamp(audit.execution_timestamp);
}

function renderReport(scan) {
  const report = scan.report || {};
  const ready = Boolean(report.generated);
  byId('report-badge').className = `report-badge ${ready ? 'ready' : ''}`;
  byId('report-badge').textContent = ready ? 'AVAILABLE' : 'NOT GENERATED';
  byId('report-title').textContent = ready ? 'Incident PDF generated' : 'No incident PDF generated';
  byId('report-path').textContent = ready ? report.path : 'Reports are generated only when drift is detected.';
}

async function refreshDashboard() {
  const button = byId('scan-button');
  button.disabled = true;
  button.querySelector('span:last-child').textContent = 'Scanning...';
  setFeedback('Loading current scan, topology, and history...', 'loading');
  try {
    const scan = await getJson('/api/scan');
    state.scan = scan;
    const [topology, history] = await Promise.all([getJson('/api/topology'), getJson('/api/history')]);
    renderOverview(scan);
    renderDrift(scan);
    renderTopology(topology);
    renderHistory(history);
    renderRemediation(scan);
    renderReport(scan);
    byId('connection-label').textContent = 'API connected';
    setFeedback('Live data loaded from AeroDrift scan service.', 'success');
  } catch (error) {
    byId('connection-label').textContent = 'API error';
    setFeedback(`Unable to load dashboard data: ${error.message}`, 'error');
  } finally {
    button.disabled = false;
    button.querySelector('span:last-child').textContent = 'Refresh scan';
  }
}

byId('scan-button').addEventListener('click', refreshDashboard);
refreshDashboard();