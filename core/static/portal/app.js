// Helpers de token ------------------------------------------------------------
function getToken() {
  try { return localStorage.getItem("jwt_access") || ""; } catch { return ""; }
}
function setToken(t) { try { localStorage.setItem("jwt_access", t); } catch {} }
function isLogged() { return !!getToken(); }

// UI badges
function refreshBadge() {
  const b = document.getElementById("badgeAuth");
  if (!b) return;
  b.textContent = isLogged() ? "logado" : "deslogado";
  b.className = "badge " + (isLogged() ? "ok" : "");
}

// Login automático já existente via /api/auth/login/ (se quiser futuramente)
// Aqui mantemos apenas o consumo do token guardado no localStorage.

// Fetch wrapper com Bearer ----------------------------------------------------
async function apiGet(url) {
  const headers = { "Accept": "application/json" };
  const tk = getToken();
  if (tk) headers["Authorization"] = "Bearer " + tk;
  const r = await fetch(url, { headers });
  if (!r.ok) throw new Error(`GET ${url}: ${r.status}`);
  return r.json();
}

// Dashboard: só placeholders por enquanto (já existia)
async function loadDashboard() {
  refreshBadge();
  // (Podemos puxar KPIs reais depois)
}

// ITENS -----------------------------------------------------------------------
let chartItens = null;

async function loadItens() {
  refreshBadge();

  const de = document.getElementById("i-de").value || "";
  const ate = document.getElementById("i-ate").value || "";
  const top = document.getElementById("i-top").value || 20;

  const url = `/api/relatorios/itens-mais-vendidos/?de=${de}&ate=${ate}&top=${top}`;
  const data = await apiGet(url);

  // Tabela
  const tbody = document.querySelector("#tbl-itens tbody");
  tbody.innerHTML = "";
  (data.itens || []).forEach(r => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${r["produto__sku"]}</td>
      <td>${r["produto__descricao"]}</td>
      <td class="num">${(+r["qtd_total"]).toLocaleString("pt-BR")}</td>
      <td class="num">R$ ${(+r["valor_total"]).toLocaleString("pt-BR", {minimumFractionDigits:2})}</td>
    `;
    tbody.appendChild(tr);
  });

  // Gráfico (TOP N por QTD)
  const labels = (data.itens || []).map(r => r["produto__sku"]);
  const valores = (data.itens || []).map(r => +r["qtd_total"]);
  const ctx = document.getElementById("chart-itens").getContext("2d");
  if (chartItens) chartItens.destroy();
  chartItens = new Chart(ctx, {
    type: "bar",
    data: { labels, datasets: [{ label: "Qtd", data: valores }] },
    options: { responsive: true, plugins: { legend: { display: false } } }
  });

  // Botões de exportação
  document.getElementById("btnCsvItens").onclick = () =>
    window.open(`${url}&format=csv`, "_blank");
  document.getElementById("btnXlsxItens").onclick = () =>
    window.open(`${url}&format=xlsx`, "_blank");
}

function wireItens() {
  document.getElementById("btnBuscarItens").onclick = loadItens;
  // preenche datas do mês atual
  const d = new Date();
  const y = d.getFullYear(), m = (d.getMonth() + 1).toString().padStart(2, "0");
  document.getElementById("i-de").value = `${y}-${m}-01`;
  document.getElementById("i-ate").value = `${y}-${m}-${new Date(y, +m, 0).getDate().toString().padStart(2,"0")}`;
  loadItens().catch(console.error);
}

// RESUMO ----------------------------------------------------------------------
let chartResumo = null;

async function loadResumo() {
  refreshBadge();

  const de = document.getElementById("r-de").value || "";
  const ate = document.getElementById("r-ate").value || "";
  const url = `/api/relatorios/vendas-resumo/?de=${de}&ate=${ate}`;
  const data = await apiGet(url);

  // KPIs
  document.getElementById("r-qtd").textContent = (data.totais?.qtd_pedidos ?? 0).toLocaleString("pt-BR");
  document.getElementById("r-total").textContent = `R$ ${(data.totais?.total_vendido ?? 0).toLocaleString("pt-BR",{minimumFractionDigits:2})}`;
  document.getElementById("r-ticket").textContent = `R$ ${(data.totais?.ticket_medio ?? 0).toLocaleString("pt-BR",{minimumFractionDigits:2})}`;

  // Tabela
  const tbody = document.querySelector("#tbl-resumo tbody");
  tbody.innerHTML = "";
  (data.por_cliente || []).forEach(r => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${r["cliente__nome"]}</td>
      <td class="num">${(r["pedidos"] ?? 0).toLocaleString("pt-BR")}</td>
      <td class="num">R$ ${(+r["total"] || 0).toLocaleString("pt-BR",{minimumFractionDigits:2})}</td>
    `;
    tbody.appendChild(tr);
  });

  // Gráfico por cliente (TOP N)
  const labels = (data.por_cliente || []).slice(0, 10).map(r => r["cliente__nome"]);
  const valores = (data.por_cliente || []).slice(0, 10).map(r => +r["total"]);
  const ctx = document.getElementById("chart-resumo").getContext("2d");
  if (chartResumo) chartResumo.destroy();
  chartResumo = new Chart(ctx, {
    type: "doughnut",
    data: { labels, datasets: [{ data: valores }] },
    options: { responsive: true }
  });

  // Exportação
  document.getElementById("btnCsvResumo").onclick  = () => window.open(`${url}&format=csv`, "_blank");
  document.getElementById("btnXlsxResumo").onclick = () => window.open(`${url}&format=xlsx`, "_blank");
  document.getElementById("btnPdfResumo").onclick  = () => window.open(`${url}&format=pdf`, "_blank");
}

function wireResumo() {
  document.getElementById("btnBuscarResumo").onclick = loadResumo;
  const d = new Date();
  const y = d.getFullYear(), m = (d.getMonth() + 1).toString().padStart(2, "0");
  document.getElementById("r-de").value  = `${y}-${m}-01`;
  document.getElementById("r-ate").value = `${y}-${m}-${new Date(y, +m, 0).getDate().toString().padStart(2,"0")}`;
  loadResumo().catch(console.error);
}

// Router simples por página ----------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  refreshBadge();
  const page = document.body.dataset.page || "";
  if (page === "itens")   wireItens();
  if (page === "resumo")  wireResumo();
  if (page === "dash" || page === "") loadDashboard();
});

// ===================== JOBS UI ==========================
let jobsTimer = null;
let currentJob = null;

async function apiPost(url, body) {
  const headers = { "Content-Type": "application/json", "Accept": "application/json" };
  const tk = getToken();
  if (tk) headers["Authorization"] = "Bearer " + tk;
  const r = await fetch(url, { method: "POST", headers, body: JSON.stringify(body || {}) });
  if (!r.ok) throw new Error(`POST ${url}: ${r.status}`);
  return r.json();
}

async function loadJobs() {
  const data = await apiGet("/api/jobs/");
  const tbody = document.querySelector("#tbl-jobs tbody");
  tbody.innerHTML = "";
  (data.results || []).forEach(j => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${j.started_at ? new Date(j.started_at).toLocaleString("pt-BR") : "-"}</td>
      <td>${j.name}</td>
      <td>${j.type}</td>
      <td>${j.status}</td>
      <td>${j.progress}%</td>
      <td><button class="btn ghost" data-id="${j.id}">Logs</button></td>
    `;
    tbody.appendChild(tr);
  });

  tbody.querySelectorAll("button[data-id]").forEach(btn => {
    btn.onclick = () => {
      currentJob = btn.dataset.id;
      document.getElementById("logsBox").textContent = "(carregando logs...)";
      loadLogs().catch(console.error);
    };
  });
}

async function loadLogs() {
  if (!currentJob) return;
  const data = await apiGet(`/api/jobs/${currentJob}/logs/`);
  const box = document.getElementById("logsBox");
  box.textContent = (data.results || [])
    .slice().reverse()
    .map(l => `[${new Date(l.ts).toLocaleString("pt-BR")}] ${l.level}: ${l.message}`)
    .join("\n");
  box.scrollTop = box.scrollHeight;
}

async function runJob(type) {
  document.getElementById("jobsBadge").textContent = "executando...";
  await apiPost("/api/jobs/run/", { type });
  await loadJobs();
  document.getElementById("jobsBadge").textContent = "pronto";
}

function wireJobs() {
  refreshBadge();
  document.getElementById("btnRunSankhya").onclick = () => runJob("sankhya_demo").catch(alert);
  document.getElementById("btnRunFull").onclick     = () => runJob("full_load_demo").catch(alert);

  loadJobs().catch(console.error);
  if (jobsTimer) clearInterval(jobsTimer);
  jobsTimer = setInterval(() => {
    loadJobs().catch(()=>{});
    loadLogs().catch(()=>{});
  }, 3000);
}

// Router: já temos embaixo; só adiciona o case jobs:
document.addEventListener("DOMContentLoaded", () => {
  refreshBadge();
  const page = document.body.dataset.page || "";
  if (page === "jobs")    wireJobs();
  if (page === "itens")   wireItens?.();
  if (page === "resumo")  wireResumo?.();
  if (page === "dash" || page === "") loadDashboard?.();
});
