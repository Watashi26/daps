import { renderField } from '../settings_helpers.js';
import { renderHelp } from '../../helper.js';
import { upgradinatorrModal } from '../modals.js';
import { DAPS, humanize, showToast } from '../../common.js';

const MODULE = 'upgradinatorr';
const STATUS_POLL_MS = 2000;

let upgradinatorrData = [];

export function renderUpgradinatorrSettings(formFields, config, rootConfig) {
    const wrapper = document.createElement('div');
    wrapper.className = 'settings-wrapper';

    const help = renderHelp('upgradinatorr');
    if (help) wrapper.appendChild(help);

    Object.entries(config).forEach(([key, value]) => {
        if (key !== 'instances_list') {
            if (typeof value === 'object' && !Array.isArray(value) && value !== null) {
                return;
            }
            renderField(wrapper, key, value);
        }
    });

    const instanceField = document.createElement('div');
    instanceField.className = 'field setting-field';
    instanceField.innerHTML = `
        <label>Instances</label>
        <button type="button" id="add-instance-btn" class="btn add-control-btn">➕ Add Instance</button>
        <div class="card-body upgradinatorr-table-wrap">
            <table id="upgradinatorr-table" class="upgradinatorr-table">
                <thead>
                    <tr>
                        <th>Instance</th>
                        <th>Count</th>
                        <th>Tag Name</th>
                        <th>Ignore Tag</th>
                        <th>Use Tag</th>
                        <th>Unattended</th>
                        <th>Threshold</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
        </div>
    `;
    wrapper.appendChild(instanceField);

    const tbody = instanceField.querySelector('tbody');
    upgradinatorrData = Object.entries(config.instances_list || {}).map(([inst, opts]) => {
        const entry = {
            instance: opts.instance,
            count: opts.count,
            tag_name: opts.tag_name,
            ignore_tag: opts.ignore_tag,
            use_tag: opts.use_tag ?? '',
            unattended: opts.unattended,
        };
        if (typeof opts.season_monitored_threshold !== 'undefined') {
            entry.season_monitored_threshold = opts.season_monitored_threshold;
        }
        return entry;
    });

    // Only one upgradinatorr run can be active at a time (scheduled, full or single-instance).
    let runState = { running: false, instance: null };
    let lastRunInstance = null;
    let pollTimer = null;

    function applyRunState() {
        tbody.querySelectorAll('tr').forEach((row) => {
            const entry = upgradinatorrData[parseInt(row.dataset.idx, 10)];
            const runBtn = row.querySelector('.instance-run-btn');
            const logsBtn = row.querySelector('.instance-logs-btn');
            if (!entry || !runBtn || !logsBtn) return;
            const isThis = runState.running && runState.instance === entry.instance;
            runBtn.classList.toggle('running', isThis);
            if (!isThis) runBtn.classList.remove('cancel-hover');
            runBtn.textContent = !isThis
                ? 'Run'
                : runBtn.classList.contains('cancel-hover')
                ? 'Cancel'
                : 'Running';
            runBtn.disabled = runState.running && !isThis;
            runBtn.title = isThis
                ? 'Cancel this run'
                : runState.running
                ? 'Upgradinatorr is already running'
                : 'Run Upgradinatorr for this instance only';
            logsBtn.style.display = entry.instance === lastRunInstance ? '' : 'none';
        });
    }

    async function refreshRunState() {
        clearTimeout(pollTimer);
        // Stop polling once the table is gone (page or module changed)
        if (!tbody.isConnected) return;
        try {
            const res = await fetch(`/api/status?module=${MODULE}`);
            const status = await res.json();
            if (runState.running && runState.instance && !status.running) {
                showToast(`✅ Upgradinatorr finished for ${humanize(runState.instance)}`, 'success');
            }
            runState = {
                running: !!status.running,
                instance: status.running ? status.instance ?? null : null,
            };
            if (runState.instance) lastRunInstance = runState.instance;
            applyRunState();
        } catch (e) {
            console.error('Failed to fetch upgradinatorr status:', e);
        }
        pollTimer = setTimeout(refreshRunState, STATUS_POLL_MS);
    }

    async function runInstance(entry, runBtn) {
        if (runBtn.classList.contains('running')) {
            const res = await fetch('/api/cancel', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ module: MODULE }),
            });
            if (res.ok) {
                runState = { running: false, instance: null };
                showToast(`🛑 Upgradinatorr cancelled for ${humanize(entry.instance)}`, 'info');
            }
            refreshRunState();
            return;
        }
        // Runs use the saved config, so unsaved table edits would be ignored
        if (DAPS.isDirty) {
            showToast('⚠️ Save your changes before running an instance.', 'error');
            return;
        }
        runBtn.disabled = true;
        const res = await fetch('/api/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ module: MODULE, instance: entry.instance }),
        });
        if (!res.ok) {
            let msg = res.statusText;
            try {
                msg = (await res.json()).error || msg;
            } catch {}
            showToast(`❌ Failed to start ${humanize(entry.instance)}: ${msg}`, 'error');
            runBtn.disabled = false;
            return;
        }
        showToast(`▶️ Upgradinatorr started for ${humanize(entry.instance)}`, 'success');
        runState = { running: true, instance: entry.instance };
        lastRunInstance = entry.instance;
        applyRunState();
        clearTimeout(pollTimer);
        pollTimer = setTimeout(refreshRunState, STATUS_POLL_MS);
    }

    function updateTable() {
        tbody.innerHTML = upgradinatorrData
            .map(
                (entry, i) => `
            <tr data-idx="${i}">
                <td>${humanize(entry.instance)}</td>
                <td>${entry.count}</td>
                <td>${entry.tag_name}</td>
                <td>${entry.ignore_tag}</td>
                <td>${entry.use_tag ?? ''}</td>
                <td>${entry.unattended}</td>
                <td>${entry.season_monitored_threshold ?? ''}</td>
                <td>
                    <div class="table-actions">
                        <button type="button" class="run-btn instance-run-btn btn" data-idx="${i}">Run</button>
                        <a href="/pages/logs" class="instance-logs-btn btn" title="Open the Upgradinatorr log">Logs</a>
                        <button type="button" class="edit-upgrade btn" data-idx="${i}">Edit</button>
                        <button type="button" class="remove-btn btn--cancel btn--remove-item btn" data-idx="${i}">-</button>
                    </div>
                </td>
            </tr>
        `
            )
            .join('');
        tbody.querySelectorAll('.instance-run-btn').forEach((btn) => {
            const entry = upgradinatorrData[parseInt(btn.dataset.idx, 10)];
            btn.onclick = () => runInstance(entry, btn);
            btn.onmouseenter = () => {
                if (!btn.classList.contains('running')) return;
                btn.classList.add('cancel-hover');
                btn.textContent = 'Cancel';
            };
            btn.onmouseleave = () => {
                if (!btn.classList.contains('running')) return;
                btn.classList.remove('cancel-hover');
                btn.textContent = 'Running';
            };
        });
        // The global link handler does the navigation (incl. unsaved-changes prompt)
        tbody.querySelectorAll('.instance-logs-btn').forEach((link) => {
            link.onclick = () => {
                window._preselectedLogModule = MODULE;
            };
        });
        applyRunState();
        tbody.querySelectorAll('.remove-btn').forEach((btn) => {
            btn.onclick = () => {
                const confirmed = confirm('Are you sure you want to remove this instance?');
                if (confirmed) {
                    const idx = parseInt(btn.dataset.idx, 10);
                    upgradinatorrData.splice(idx, 1);
                    updateTable();
                }
            };
        });
        tbody.querySelectorAll('.edit-upgrade').forEach((btn) => {
            btn.onclick = () => {
                const idx = parseInt(btn.dataset.idx, 10);
                upgradinatorrModal(idx, upgradinatorrData, rootConfig, updateTable);
            };
        });
    }

    instanceField
        .querySelector('#add-instance-btn')
        .addEventListener('click', () =>
            upgradinatorrModal(undefined, upgradinatorrData, rootConfig, updateTable)
        );
    updateTable();
    refreshRunState();

    formFields.appendChild(wrapper);
}

export function getUpgradinatorrData() {
    return upgradinatorrData;
}
