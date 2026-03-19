const express = require('express');
const app = express();
const port = process.env.PORT || 5000;

app.use(express.json());

let events = [];

app.get('/', (req, res) => {
    res.redirect('/dashboard');
});

app.get('/api/info', (req, res) => {
    res.json({
        service: "Bentley iTwin Webhooks Dashboard MVP",
        version: "1.0",
        status: "running",
        engine: "Node.js/Express"
    });
});

app.get('/health', (req, res) => {
    res.json({ status: "healthy", timestamp: new Date().toISOString() });
});

app.post('/webhook', (req, res) => {
    const event = {
        ...req.body,
        receivedAt: new Date().toISOString(),
        id: Date.now()
    };
    events.unshift(event);
    if (events.length > 1000) events = events.slice(0, 1000);
    res.status(200).send('OK');
});

app.get('/events', (req, res) => {
    res.json(events.slice(0, 200));
});

app.get('/dashboard', (req, res) => {
    const kpis = {
        created: events.filter(e => e.eventType === 'iModels.iModelCreated.v1').length,
        deleted: events.filter(e => e.eventType === 'iModels.iModelDeleted.v1').length,
        versions: events.filter(e => e.eventType === 'iModels.namedVersionCreated.v1').length,
        changes: events.filter(e => e.eventType === 'iModels.changesReady.v1').length
    };

    const html = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>iTwin Dashboard</title>
    <style>
        body { font-family: sans-serif; background: #f0f2f5; margin: 0; padding: 20px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }
        .card h3 { margin: 0; color: #666; font-size: 0.9rem; }
        .card .value { font-size: 2rem; font-weight: bold; color: #1a73e8; margin-top: 10px; }
        .health { padding: 10px; border-radius: 4px; margin-bottom: 20px; font-weight: bold; text-align: center; }
        .healthy { background: #e6f4ea; color: #1e8e3e; }
        table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
        th { background: #f8f9fa; color: #666; font-size: 0.8rem; text-transform: uppercase; }
        .timestamp { color: #888; font-size: 0.8rem; }
    </style>
</head>
<body>
    <h1>iTwin Webhooks Dashboard</h1>
    <div class="health healthy">System Status: Healthy</div>
    <div class="grid">
        <div class="card"><h3>iModels Created</h3><div class="value">${kpis.created}</div></div>
        <div class="card"><h3>iModels Deleted</h3><div class="value">${kpis.deleted}</div></div>
        <div class="card"><h3>Named Versions</h3><div class="value">${kpis.versions}</div></div>
        <div class="card"><h3>Changes Ready</h3><div class="value">${kpis.changes}</div></div>
    </div>
    <table>
        <thead><tr><th>Event Type</th><th>Resource</th><th>Received At</th></tr></thead>
        <tbody>
            ${events.slice(0, 20).map(e => `
                <tr>
                    <td><strong>${e.eventType || 'Unknown'}</strong></td>
                    <td>${e.content?.iModelId || e.content?.iTwinId || '-'}</td>
                    <td class="timestamp">${new Date(e.receivedAt).toLocaleString()}</td>
                </tr>
            `).join('')}
        </tbody>
    </table>
    <script>setTimeout(() => location.reload(), 15000);</script>
</body>
</html>`;
    res.send(html);
});

app.listen(port, '0.0.0.0', () => {
    console.log('Server running at http://0.0.0.0:' + port);
});
