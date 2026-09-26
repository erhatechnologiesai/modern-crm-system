// ApexCRM Client Application Logic
let authToken = localStorage.getItem("apex_crm_token") || "";
let currentUser = JSON.parse(localStorage.getItem("apex_crm_user") || "null");
let pipelineChart = null;

let state = {
  dashboard: null,
  deals: [],
  contacts: [],
  companies: [],
  leads: [],
  tasks: []
};

// Initialize Application
document.addEventListener("DOMContentLoaded", async () => {
  if (currentUser) {
    updateUserUI();
  } else {
    // Attempt automatic login with demo admin account
    await autoDemoLogin();
  }
  await loadAllData();
});

async function autoDemoLogin() {
  try {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: "admin@apexcrm.io", password: "Admin@Apex2026!" })
    });
    if (res.ok) {
      const data = await res.json();
      authToken = data.access_token;
      currentUser = data.user;
      localStorage.setItem("apex_crm_token", authToken);
      localStorage.setItem("apex_crm_user", JSON.stringify(currentUser));
      updateUserUI();
    }
  } catch (e) {
    console.error("Auto login error", e);
  }
}

function updateUserUI() {
  const userBadge = document.getElementById("userBadge");
  const authBtn = document.getElementById("authBtn");
  if (currentUser) {
    userBadge.classList.remove("hidden");
    document.getElementById("userName").textContent = currentUser.full_name;
    document.getElementById("userRole").textContent = currentUser.role;
    authBtn.innerHTML = '<i class="fa-solid fa-right-from-bracket mr-1"></i> Logout';
    authBtn.onclick = handleLogout;
  } else {
    userBadge.classList.add("hidden");
    authBtn.innerHTML = '<i class="fa-solid fa-right-to-bracket mr-1"></i> Login';
    authBtn.onclick = toggleAuthModal;
  }
}

function handleLogout() {
  authToken = "";
  currentUser = null;
  localStorage.removeItem("apex_crm_token");
  localStorage.removeItem("apex_crm_user");
  updateUserUI();
  loadAllData();
}

function toggleAuthModal() {
  const modal = document.getElementById("authModal");
  modal.classList.toggle("hidden");
}

async function handleAuth(e) {
  e.preventDefault();
  const email = document.getElementById("authEmail").value;
  const password = document.getElementById("authPassword").value;
  try {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });
    if (!res.ok) {
      alert("Invalid credentials!");
      return;
    }
    const data = await res.json();
    authToken = data.access_token;
    currentUser = data.user;
    localStorage.setItem("apex_crm_token", authToken);
    localStorage.setItem("apex_crm_user", JSON.stringify(currentUser));
    updateUserUI();
    toggleAuthModal();
    loadAllData();
  } catch (err) {
    alert("Authentication failed: " + err.message);
  }
}

function switchTab(tabId) {
  const tabs = ["dashboard", "deals", "contacts", "companies", "leads", "tasks"];
  tabs.forEach(t => {
    document.getElementById(`content-${t}`).classList.add("hidden");
    document.getElementById(`tab-${t}`).classList.remove("active", "bg-indigo-600", "text-white");
    document.getElementById(`tab-${t}`).classList.add("bg-slate-800", "text-slate-300");
  });

  document.getElementById(`content-${tabId}`).classList.remove("hidden");
  document.getElementById(`tab-${tabId}`).classList.add("active", "bg-indigo-600", "text-white");
  document.getElementById(`tab-${tabId}`).classList.remove("bg-slate-800", "text-slate-300");
}

async function apiFetch(endpoint, options = {}) {
  const headers = options.headers || {};
  if (authToken) {
    headers["Authorization"] = `Bearer ${authToken}`;
  }
  options.headers = headers;
  return fetch(endpoint, options);
}

async function loadAllData() {
  await Promise.all([
    fetchDashboard(),
    fetchDeals(),
    fetchContacts(),
    fetchCompanies(),
    fetchLeads(),
    fetchTasks()
  ]);
}

async function fetchDashboard() {
  try {
    const res = await apiFetch("/api/analytics/dashboard");
    if (!res.ok) return;
    const data = await res.json();
    state.dashboard = data;

    document.getElementById("statWonRevenue").textContent = "$" + data.total_revenue_won.toLocaleString();
    document.getElementById("statPipelineValue").textContent = "$" + data.pipeline_total_value.toLocaleString();
    document.getElementById("statDealsCount").textContent = data.total_deals;
    document.getElementById("statTasksCount").textContent = data.active_tasks;

    renderPipelineChart(data.deals_by_stage);
    renderRecentActivities(data.recent_activities);
  } catch (err) {
    console.error("Dashboard error:", err);
  }
}

function renderPipelineChart(dealsByStage) {
  const ctx = document.getElementById("pipelineChart");
  if (!ctx) return;
  const stages = ["prospect", "qualification", "proposal", "negotiation", "closed_won", "closed_lost"];
  const values = stages.map(s => dealsByStage[s] ? dealsByStage[s].value : 0);

  if (pipelineChart) {
    pipelineChart.destroy();
  }

  pipelineChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: ["Prospect", "Qualification", "Proposal", "Negotiation", "Won", "Lost"],
      datasets: [{
        label: "Stage Pipeline Value ($)",
        data: values,
        backgroundColor: [
          "#6366f1",
          "#3b82f6",
          "#f59e0b",
          "#8b5cf6",
          "#10b981",
          "#ef4444"
        ],
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        y: {
          ticks: { color: "#94a3b8" },
          grid: { color: "#334155" }
        },
        x: {
          ticks: { color: "#94a3b8" },
          grid: { display: false }
        }
      }
    }
  });
}

function renderRecentActivities(activities) {
  const container = document.getElementById("recentActivityList");
  if (!container) return;
  if (!activities || activities.length === 0) {
    container.innerHTML = `<p class="text-slate-500">No activity yet recorded.</p>`;
    return;
  }
  container.innerHTML = activities.map(act => `
    <div class="border-l-2 border-indigo-500 pl-3 py-1">
      <div class="flex justify-between items-center">
        <span class="font-bold text-slate-300 text-xs">${act.action}</span>
        <span class="text-slate-500 text-[10px]">${act.created_at || 'Just now'}</span>
      </div>
      <p class="text-slate-400 text-xs mt-0.5">${act.details || ''}</p>
    </div>
  `).join('');
}

async function fetchDeals() {
  try {
    const res = await apiFetch("/api/deals");
    if (!res.ok) return;
    state.deals = await res.json();
    renderDealsKanban();
  } catch (err) {
    console.error(err);
  }
}

function renderDealsKanban() {
  const container = document.getElementById("kanbanBoard");
  if (!container) return;
  const stages = [
    { key: "prospect", label: "Prospecting", color: "indigo" },
    { key: "qualification", label: "Qualification", color: "blue" },
    { key: "proposal", label: "Proposal", color: "amber" },
    { key: "negotiation", label: "Negotiation", color: "purple" },
    { key: "closed_won", label: "Closed Won", color: "emerald" }
  ];

  container.innerHTML = stages.map(stage => {
    const stageDeals = state.deals.filter(d => d.stage === stage.key);
    const sum = stageDeals.reduce((acc, curr) => acc + curr.amount, 0);
    return `
      <div class="bg-slate-800/60 border border-slate-700/80 rounded-xl p-3 flex flex-col">
        <div class="flex justify-between items-center mb-3">
          <span class="font-semibold text-xs uppercase text-${stage.color}-400">${stage.label}</span>
          <span class="text-xs bg-slate-700 px-2 py-0.5 rounded-full text-slate-300">${stageDeals.length}</span>
        </div>
        <p class="text-xs text-slate-400 font-mono mb-3">$${sum.toLocaleString()}</p>
        <div class="space-y-2 flex-1">
          ${stageDeals.map(d => `
            <div class="bg-slate-700/80 p-3 rounded-lg border border-slate-600 shadow-sm text-xs space-y-1">
              <div class="font-semibold text-slate-100">${d.title}</div>
              <div class="text-slate-400">${d.company_name || 'Individual'}</div>
              <div class="flex justify-between items-center pt-1 font-mono font-bold text-emerald-400">
                <span>$${d.amount.toLocaleString()}</span>
                <span class="text-[10px] text-slate-400 font-normal">${d.probability}% prob</span>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }).join('');
}

async function fetchContacts() {
  try {
    const res = await apiFetch("/api/contacts");
    if (!res.ok) return;
    state.contacts = await res.json();
    renderContacts(state.contacts);
  } catch (err) {
    console.error(err);
  }
}

function renderContacts(contacts) {
  const tbody = document.getElementById("contactsTableBody");
  if (!tbody) return;
  tbody.innerHTML = contacts.map(c => `
    <tr class="hover:bg-slate-700/30">
      <td class="p-3 font-medium text-slate-200">${c.first_name} ${c.last_name}</td>
      <td class="p-3 text-slate-400">${c.company_name || '-'}</td>
      <td class="p-3 text-slate-300">${c.email}</td>
      <td class="p-3 text-slate-400">${c.phone || '-'}</td>
      <td class="p-3"><span class="px-2 py-0.5 text-xs rounded-full bg-indigo-900/50 text-indigo-300 border border-indigo-700">${c.status}</span></td>
      <td class="p-3 text-right">
        <button onclick="deleteContactItem(${c.id})" class="text-rose-400 hover:text-rose-300 text-xs"><i class="fa-solid fa-trash"></i></button>
      </td>
    </tr>
  `).join('');
}

function filterContacts() {
  const query = document.getElementById("contactSearch").value.toLowerCase();
  const filtered = state.contacts.filter(c => 
    c.first_name.toLowerCase().includes(query) ||
    c.last_name.toLowerCase().includes(query) ||
    c.email.toLowerCase().includes(query)
  );
  renderContacts(filtered);
}

async function deleteContactItem(id) {
  if (!confirm("Are you sure you want to delete this contact?")) return;
  const res = await apiFetch(`/api/contacts/${id}`, { method: "DELETE" });
  if (res.ok) {
    await fetchContacts();
    await fetchDashboard();
  }
}

async function fetchCompanies() {
  try {
    const res = await apiFetch("/api/companies");
    if (!res.ok) return;
    state.companies = await res.json();
    renderCompanies(state.companies);
  } catch (err) {
    console.error(err);
  }
}

function renderCompanies(companies) {
  const tbody = document.getElementById("companiesTableBody");
  if (!tbody) return;
  tbody.innerHTML = companies.map(c => `
    <tr class="hover:bg-slate-700/30">
      <td class="p-3 font-medium text-slate-200">${c.name}</td>
      <td class="p-3 text-slate-400">${c.industry || '-'}</td>
      <td class="p-3 text-slate-400">${c.size || '-'}</td>
      <td class="p-3 text-slate-400">${c.city || ''}, ${c.country || ''}</td>
      <td class="p-3 font-mono text-emerald-400">$${(c.annual_revenue || 0).toLocaleString()}</td>
      <td class="p-3 text-right">
        <button onclick="deleteCompanyItem(${c.id})" class="text-rose-400 hover:text-rose-300 text-xs"><i class="fa-solid fa-trash"></i></button>
      </td>
    </tr>
  `).join('');
}

async function deleteCompanyItem(id) {
  if (!confirm("Delete this company record?")) return;
  const res = await apiFetch(`/api/companies/${id}`, { method: "DELETE" });
  if (res.ok) {
    await fetchCompanies();
    await fetchDashboard();
  }
}

async function fetchLeads() {
  try {
    const res = await apiFetch("/api/leads");
    if (!res.ok) return;
    state.leads = await res.json();
    renderLeads(state.leads);
  } catch (err) {
    console.error(err);
  }
}

function renderLeads(leads) {
  const tbody = document.getElementById("leadsTableBody");
  if (!tbody) return;
  tbody.innerHTML = leads.map(l => `
    <tr class="hover:bg-slate-700/30">
      <td class="p-3 font-medium text-slate-200">${l.title}</td>
      <td class="p-3 text-slate-400">${l.company_name || l.contact_name || '-'}</td>
      <td class="p-3 font-mono text-indigo-400">$${(l.value || 0).toLocaleString()}</td>
      <td class="p-3 text-slate-400">${l.source || '-'}</td>
      <td class="p-3"><span class="px-2 py-0.5 text-xs rounded-full bg-amber-900/50 text-amber-300 border border-amber-700">${l.status}</span></td>
      <td class="p-3 text-right">
        <button onclick="deleteLeadItem(${l.id})" class="text-rose-400 hover:text-rose-300 text-xs"><i class="fa-solid fa-trash"></i></button>
      </td>
    </tr>
  `).join('');
}

async function deleteLeadItem(id) {
  if (!confirm("Delete lead record?")) return;
  const res = await apiFetch(`/api/leads/${id}`, { method: "DELETE" });
  if (res.ok) {
    await fetchLeads();
    await fetchDashboard();
  }
}

async function fetchTasks() {
  try {
    const res = await apiFetch("/api/tasks");
    if (!res.ok) return;
    state.tasks = await res.json();
    renderTasks(state.tasks);
  } catch (err) {
    console.error(err);
  }
}

function renderTasks(tasks) {
  const tbody = document.getElementById("tasksTableBody");
  if (!tbody) return;
  tbody.innerHTML = tasks.map(t => `
    <tr class="hover:bg-slate-700/30">
      <td class="p-3 font-medium text-slate-200">${t.title}</td>
      <td class="p-3 text-slate-400">${t.due_date || 'No due date'}</td>
      <td class="p-3">
        <span class="px-2 py-0.5 text-xs rounded-full ${t.priority === 'urgent' ? 'bg-rose-900 text-rose-300' : 'bg-slate-700 text-slate-300'}">${t.priority}</span>
      </td>
      <td class="p-3">
        <select onchange="updateTaskStatusItem(${t.id}, this.value)" class="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-slate-200">
          <option value="pending" ${t.status === 'pending' ? 'selected' : ''}>Pending</option>
          <option value="in_progress" ${t.status === 'in_progress' ? 'selected' : ''}>In Progress</option>
          <option value="completed" ${t.status === 'completed' ? 'selected' : ''}>Completed</option>
        </select>
      </td>
      <td class="p-3 text-right">
        <button onclick="deleteTaskItem(${t.id})" class="text-rose-400 hover:text-rose-300 text-xs"><i class="fa-solid fa-trash"></i></button>
      </td>
    </tr>
  `).join('');
}

async function updateTaskStatusItem(id, status) {
  const res = await apiFetch(`/api/tasks/${id}/status?status=${status}`, { method: "PATCH" });
  if (res.ok) {
    await fetchTasks();
    await fetchDashboard();
  }
}

async function deleteTaskItem(id) {
  if (!confirm("Delete task?")) return;
  const res = await apiFetch(`/api/tasks/${id}`, { method: "DELETE" });
  if (res.ok) {
    await fetchTasks();
    await fetchDashboard();
  }
}

// Quick action modals
function openContactModal() {
  const first = prompt("Contact First Name:");
  if (!first) return;
  const last = prompt("Contact Last Name:") || "";
  const email = prompt("Contact Email:");
  if (!email) return;
  
  apiFetch("/api/contacts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ first_name: first, last_name: last, email: email, status: "lead" })
  }).then(() => { fetchContacts(); fetchDashboard(); });
}

function openCompanyModal() {
  const name = prompt("Company Name:");
  if (!name) return;
  const industry = prompt("Industry:", "Software & Cloud");
  
  apiFetch("/api/companies", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, industry, annual_revenue: 1000000 })
  }).then(() => { fetchCompanies(); fetchDashboard(); });
}

function openDealModal() {
  const title = prompt("Deal Title:");
  if (!title) return;
  const amount = parseFloat(prompt("Deal Amount ($):", "50000")) || 0;
  
  apiFetch("/api/deals", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, amount, stage: "proposal", probability: 50 })
  }).then(() => { fetchDeals(); fetchDashboard(); });
}

function openLeadModal() {
  const title = prompt("Lead Title:");
  if (!title) return;
  const value = parseFloat(prompt("Estimated Value ($):", "25000")) || 0;
  
  apiFetch("/api/leads", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, value, status: "new" })
  }).then(() => { fetchLeads(); fetchDashboard(); });
}

function openTaskModal() {
  const title = prompt("Task Description:");
  if (!title) return;
  
  apiFetch("/api/tasks", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, priority: "high", status: "pending" })
  }).then(() => { fetchTasks(); fetchDashboard(); });
}

function openCreateModal() {
  const choice = prompt("Create new record:\n1. Contact\n2. Deal\n3. Company\n4. Task\n5. Lead\nEnter number (1-5):");
  if (choice === "1") openContactModal();
  else if (choice === "2") openDealModal();
  else if (choice === "3") openCompanyModal();
  else if (choice === "4") openTaskModal();
  else if (choice === "5") openLeadModal();
}
