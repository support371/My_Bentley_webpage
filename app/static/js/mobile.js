(function () {
  const state = {
    summary: null,
    integrationsRaw: [],
  };

  function esc(value) {
    if (value == null) return '';
    const d = document.createElement('div');
    d.textContent = String(value);
    return d.innerHTML;
  }

  async function getJson(url, options) {
    const res = await fetch(url, options || {});
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || 'Request failed');
    }
    return data;
  }

  function setText(id, value) {
    const node = document.getElementById(id);
    if (node) node.textContent = value;
  }

  async function refreshSummary() {
    try {
      const data = await getJson('/api/mobile/summary');
      state.summary = data;
      setText('summaryHealth', humanize(data.health));
      setText('summaryAlerts', data.kpis.openAlerts);
      setText('summaryIntegrations', data.kpis.integrationsConnected);
      setText('summaryUptime', data.kpis.uptime);
    } catch (err) {
      setText('summaryHealth', 'Unavailable');
    }
  }

  function humanize(value) {
    return String(value || '').replace(/[-_]/g, ' ').replace(/\b\w/g, (m) => m.toUpperCase());
  }

  function timeAgo(iso) {
    if (!iso) return 'Unknown';
    const diff = Math.max(0, Date.now() - new Date(iso).getTime());
    const sec = Math.floor(diff / 1000);
    if (sec < 60) return sec + 's ago';
    const min = Math.floor(sec / 60);
    if (min < 60) return min + 'm ago';
    const hrs = Math.floor(min / 60);
    if (hrs < 24) return hrs + 'h ago';
    const days = Math.floor(hrs / 24);
    return days + 'd ago';
  }

  async function initAlarmsPage() {
    await refreshSummary();
    const host = document.getElementById('alarmsList');
    if (!host) return;
    try {
      const data = await getJson('/api/mobile/alarms');
      host.innerHTML = data.items.length ? data.items.map((item) => `
        <article class="mobile-list-item">
          <div class="top">
            <div>
              <div class="title">${esc(item.title)}</div>
              <div class="meta">${esc(item.category)} • ${esc(item.project)}</div>
            </div>
            <span class="mobile-severity ${esc(item.severity)}">${esc(item.severity)}</span>
          </div>
          <div class="meta">Model: ${esc(item.model)} • Status: ${esc(item.status)} • ${esc(timeAgo(item.receivedAt))}</div>
        </article>
      `).join('') : '<div class="mobile-empty">No alarms yet.</div>';
    } catch (err) {
      host.innerHTML = `<div class="mobile-empty">${esc(err.message)}</div>`;
    }
  }

  async function initMonitorsPage() {
    await refreshSummary();
    const host = document.getElementById('monitorsList');
    if (host) {
      try {
        const data = await getJson('/api/mobile/monitors');
        host.innerHTML = data.items.length ? data.items.map((item) => `
          <article class="mobile-list-item">
            <div class="top">
              <div>
                <div class="title">${esc(item.name)}</div>
                <div class="meta">${esc(item.type)} • ${esc(item.imodelCount)} iModels • ${esc(item.eventCount)} events</div>
              </div>
              <span class="mobile-severity ${esc(item.status || 'normal')}">${esc(item.status || 'active')}</span>
            </div>
            <div class="meta">Last event: ${esc(timeAgo(item.lastEventAt))}</div>
          </article>
        `).join('') : '<div class="mobile-empty">No monitors available.</div>';
      } catch (err) {
        host.innerHTML = `<div class="mobile-empty">${esc(err.message)}</div>`;
      }
    }

    const form = document.getElementById('discoverMonitorForm');
    if (form) {
      form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const resultNode = document.getElementById('monitorDiscoverResult');
        const formData = new FormData(form);
        const payload = Object.fromEntries(formData.entries());
        resultNode.textContent = 'Submitting discovery…';
        try {
          const data = await getJson('/api/mobile/monitors/discover', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload),
          });
          resultNode.textContent = `${data.message} Target: ${data.item.target}`;
          form.reset();
        } catch (err) {
          resultNode.textContent = err.message;
        }
      });
    }
  }

  async function initReportsPage() {
    await refreshSummary();
    const host = document.getElementById('reportsCards');
    if (!host) return;
    try {
      const data = await getJson('/api/mobile/reports');
      host.innerHTML = data.cards.map((card) => `
        <article class="mobile-report-card">
          <div class="title">${esc(card.title)}</div>
          <div class="meta">${esc(card.detail)}</div>
          <div class="meta" style="margin-top:.55rem;"><strong>${esc(card.value)}</strong></div>
        </article>
      `).join('');
    } catch (err) {
      host.innerHTML = `<div class="mobile-empty">${esc(err.message)}</div>`;
    }
  }

  async function initAdminPage() {
    await refreshSummary();
    const host = document.getElementById('adminGroups');
    if (!host) return;
    try {
      const data = await getJson('/api/mobile/admin-summary');
      host.innerHTML = data.groups.map((group) => `
        <section class="mobile-admin-card">
          <div class="title">${esc(group.section)}</div>
          ${(group.items || []).map((item) => `
            <div class="item-row">
              <span>${esc(item.label)}</span>
              <strong>${esc(item.value)}</strong>
            </div>
          `).join('')}
        </section>
      `).join('');
    } catch (err) {
      host.innerHTML = `<div class="mobile-empty">${esc(err.message)}. Admin routes may require sign-in.</div>`;
    }
  }

  async function initMorePage() {
    await refreshSummary();
    const host = document.getElementById('moreItems');
    if (host) {
      try {
        const data = await getJson('/api/mobile/more-summary');
        host.innerHTML = data.items.map((item) => `
          <article class="mobile-list-item">
            <div class="top">
              <div>
                <div class="title">${esc(item.label)}</div>
              </div>
              <span class="mobile-severity normal">${esc(item.value)}</span>
            </div>
          </article>
        `).join('');
      } catch (err) {
        host.innerHTML = `<div class="mobile-empty">${esc(err.message)}</div>`;
      }
    }
  }

  async function initIntegrationsPage() {
    await refreshSummary();
    const host = document.getElementById('mobileIntegrationGroups');
    if (!host) return;
    try {
      const data = await getJson('/api/mobile/integrations');
      state.integrationsRaw = data.groups || [];
      renderIntegrationGroups(state.integrationsRaw);
    } catch (err) {
      host.innerHTML = `<div class="mobile-empty">${esc(err.message)}</div>`;
    }
  }

  function renderIntegrationGroups(groups) {
    const host = document.getElementById('mobileIntegrationGroups');
    if (!host) return;
    host.innerHTML = groups.length ? groups.map((group) => `
      <section class="mobile-admin-card mobile-integration-group" data-group-name="${esc(group.name)}">
        <div class="title">${esc(group.name)}</div>
        <div class="mobile-integration-groups">
          ${group.items.map((item) => `
            <article class="mobile-integration-card" data-integration-name="${esc(item.name.toLowerCase())}">
              <div class="top">
                <div>
                  <div class="tag">${esc(item.category)}</div>
                  <div class="title">${esc(item.icon_emoji)} ${esc(item.name)}</div>
                  <div class="meta">${esc(item.description)}</div>
                </div>
                <span class="mobile-severity ${esc(item.status)}">${esc(item.status)}</span>
              </div>
            </article>
          `).join('')}
        </div>
      </section>
    `).join('') : '<div class="mobile-empty">No integrations available.</div>';
  }

  function filterIntegrations() {
    const q = (document.getElementById('mobileIntegrationFilter')?.value || '').toLowerCase().trim();
    if (!q) {
      renderIntegrationGroups(state.integrationsRaw);
      return;
    }
    const filtered = state.integrationsRaw.map((group) => ({
      name: group.name,
      items: group.items.filter((item) => {
        const haystack = `${item.name} ${item.description} ${item.category}`.toLowerCase();
        return haystack.includes(q);
      }),
    })).filter((group) => group.items.length);
    renderIntegrationGroups(filtered);
  }

  async function triggerTestAlert() {
    const resultNode = document.getElementById('moreActionResult');
    if (resultNode) resultNode.textContent = 'Sending test alert…';
    try {
      const data = await getJson('/api/mobile/test-alert', {method: 'POST'});
      if (resultNode) resultNode.textContent = data.message;
    } catch (err) {
      if (resultNode) resultNode.textContent = err.message;
    }
  }

  async function saveTimezone() {
    const input = document.getElementById('mobileTimezoneInput');
    const resultNode = document.getElementById('moreActionResult');
    if (resultNode) resultNode.textContent = 'Saving timezone…';
    try {
      const data = await getJson('/api/mobile/timezone', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({timezone: input?.value || 'UTC'}),
      });
      if (resultNode) resultNode.textContent = `Timezone saved: ${data.timezone}`;
    } catch (err) {
      if (resultNode) resultNode.textContent = err.message;
    }
  }

  async function saveTabs() {
    const resultNode = document.getElementById('moreActionResult');
    if (resultNode) resultNode.textContent = 'Saving tabs…';
    try {
      const tabs = ['alarms', 'monitors', 'reports', 'admin', 'more'];
      const data = await getJson('/api/mobile/tab-customization', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({tabs}),
      });
      if (resultNode) resultNode.textContent = `Tabs saved: ${data.tabs.join(', ')}`;
    } catch (err) {
      if (resultNode) resultNode.textContent = err.message;
    }
  }

  async function refreshPage() {
    const page = document.querySelector('[data-mobile-page]')?.dataset.mobilePage;
    if (page === 'alarms') return initAlarmsPage();
    if (page === 'monitors') return initMonitorsPage();
    if (page === 'reports') return initReportsPage();
    if (page === 'admin') return initAdminPage();
    if (page === 'more') return initMorePage();
    if (page === 'integrations') return initIntegrationsPage();
    return refreshSummary();
  }

  window.MobileOps = {
    refreshPage,
    initAlarmsPage,
    initMonitorsPage,
    initReportsPage,
    initAdminPage,
    initMorePage,
    initIntegrationsPage,
    triggerTestAlert,
    saveTimezone,
    saveTabs,
    filterIntegrations,
  };
})();
