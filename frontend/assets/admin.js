(function () {
  const API_BASE = window.__API_BASE__ || window.API_BASE || "http://localhost:8000";

  async function api(path, options = {}) {
    const resp = await fetch(`${API_BASE}${path}`, {
      credentials: "include",
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
      ...options,
    });

    let data = {};
    try {
      data = await resp.json();
    } catch (_) {
      // no-op
    }

    if (!resp.ok) {
      const msg = data?.error?.message || `HTTP ${resp.status}`;
      throw new Error(msg);
    }

    return data;
  }

  function qs(name) {
    const url = new URL(window.location.href);
    return url.searchParams.get(name);
  }

  async function logout() {
    try {
      await api("/api/admin/logout", { method: "POST" });
    } finally {
      window.location.href = "login.html";
    }
  }

  function mountLogout() {
    const link = document.getElementById("logout-link");
    if (link) {
      link.addEventListener("click", (e) => {
        e.preventDefault();
        logout();
      });
    }
  }

  function setupLogin() {
    const form = document.getElementById("admin-login-form");
    const err = document.getElementById("admin-error");
    if (!form) return;

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      err.textContent = "";
      const fd = new FormData(form);
      try {
        await api("/api/admin/login", {
          method: "POST",
          body: JSON.stringify({ password: fd.get("password") }),
        });
        window.location.href = "leads.html";
      } catch (error) {
        err.textContent = error.message;
      }
    });
  }

  async function setupLeads() {
    mountLogout();
    const tbody = document.getElementById("leads-tbody");
    const btn = document.getElementById("filter-apply");
    const exportBtn = document.getElementById("export-sales");

    let agencies = [];
    try {
      const agenciesResp = await api("/api/admin/agencies");
      agencies = agenciesResp.items || [];
    } catch (_) {
      agencies = [];
    }

    function askAgencyId(defaultAgencyId = "") {
      if (!agencies.length) {
        const manual = prompt("No se encontraron agencias activas. Introduce agency_id manualmente:", defaultAgencyId || "");
        return manual ? manual.trim() : null;
      }
      const options = agencies.map((a) => `${a.name}: ${a.id}`).join("\n");
      const selected = prompt(`Introduce agency_id:\n${options}`, defaultAgencyId || agencies[0].id);
      return selected ? selected.trim() : null;
    }

    function commercialLabel(item) {
      if (item.commercial_state === "sold") {
        return item.sold_at ? `sold (${new Date(item.sold_at).toLocaleString()})` : "sold";
      }
      if (item.commercial_state === "reserved") {
        return item.reserved_until
          ? `reserved hasta ${new Date(item.reserved_until).toLocaleString()}`
          : "reserved";
      }
      return "available";
    }

    async function reserveLead(item) {
      const agencyId = askAgencyId();
      if (!agencyId) return;
      const hoursRaw = prompt("Horas de reserva", "72");
      const hours = Number(hoursRaw || 72);
      await api(`/api/admin/leads/${item.lead_id}/reserve`, {
        method: "POST",
        body: JSON.stringify({ agency_id: agencyId, hours }),
      });
      await load();
    }

    async function releaseReservation(item) {
      await api(`/api/admin/leads/${item.lead_id}/release-reservation`, {
        method: "POST",
        body: JSON.stringify({ reason: "admin_manual" }),
      });
      await load();
    }

    async function sellLead(item) {
      const defaultAgency = item.reserved_to_agency_id || "";
      const agencyId = askAgencyId(defaultAgency);
      if (!agencyId) return;
      const priceRaw = prompt("Precio de venta (EUR)", "45");
      const price = Number(priceRaw || 0);
      if (!Number.isFinite(price) || price <= 0) {
        alert("Precio inválido");
        return;
      }
      await api(`/api/admin/leads/${item.lead_id}/sell`, {
        method: "POST",
        body: JSON.stringify({ agency_id: agencyId, price_eur: Math.round(price) }),
      });
      await load();
    }

    async function load() {
      const tier = document.getElementById("filter-tier").value;
      const zone = document.getElementById("filter-zone").value;
      const status = document.getElementById("filter-status").value;

      const params = new URLSearchParams();
      if (tier) params.set("tier", tier);
      if (zone) params.set("zone_key", zone.trim().toLowerCase());
      if (status) params.set("status", status);

      if (exportBtn) {
        exportBtn.onclick = (e) => {
          e.preventDefault();
          const exportParams = new URLSearchParams();
          if (tier) exportParams.set("tier", tier);
          if (zone) exportParams.set("zone_key", zone.trim().toLowerCase());
          const url = `${API_BASE}/api/admin/sales/export.csv?${exportParams.toString()}`;
          window.open(url, "_blank");
        };
      }

      try {
        const data = await api(`/api/admin/leads?${params.toString()}`);
        tbody.innerHTML = "";
        for (const item of data.items) {
          const tr = document.createElement("tr");
          const canReserve = item.tier === "A" && item.commercial_state === "available";
          const canRelease = item.commercial_state === "reserved";
          const canSell = item.commercial_state !== "sold";
          tr.innerHTML = `
            <td>${new Date(item.created_at).toLocaleString()}</td>
            <td>${item.tier || "-"}</td>
            <td>${item.iei_score ?? "-"}</td>
            <td>${item.zone_key || "-"}</td>
            <td>${item.sale_horizon || "-"}</td>
            <td>${item.owner_name || ""}<br/>${item.owner_phone || ""}</td>
            <td>${commercialLabel(item)}</td>
            <td>
              <select data-lead-status="${item.lead_id}">
                <option value="nuevo" ${item.status === "nuevo" ? "selected" : ""}>nuevo</option>
                <option value="contactado" ${item.status === "contactado" ? "selected" : ""}>contactado</option>
                <option value="cita" ${item.status === "cita" ? "selected" : ""}>cita</option>
                <option value="vendido" ${item.status === "vendido" ? "selected" : ""}>vendido</option>
                <option value="descartado" ${item.status === "descartado" ? "selected" : ""}>descartado</option>
              </select>
            </td>
            <td>
              <div class="row" style="gap:6px;flex-wrap:wrap">
                <a class="button secondary" href="lead_detail.html?id=${item.lead_id}">Ver</a>
                <button class="button" data-save-status="${item.lead_id}">Guardar</button>
                <button class="button secondary" data-reserve="${item.lead_id}" ${canReserve ? "" : "disabled"}>Reservar</button>
                <button class="button secondary" data-sell="${item.lead_id}" ${canSell ? "" : "disabled"}>Vender</button>
                <button class="button secondary" data-release="${item.lead_id}" ${canRelease ? "" : "disabled"}>Liberar</button>
              </div>
            </td>
          `;
          tbody.appendChild(tr);
        }

        const byLead = new Map(data.items.map((x) => [x.lead_id, x]));

        document.querySelectorAll("[data-save-status]").forEach((el) => {
          el.addEventListener("click", async () => {
            const leadId = el.getAttribute("data-save-status");
            const sel = document.querySelector(`[data-lead-status='${leadId}']`);
            await api(`/api/admin/leads/${leadId}`, {
              method: "PATCH",
              body: JSON.stringify({ status: sel.value }),
            });
            await load();
          });
        });

        document.querySelectorAll("[data-reserve]").forEach((el) => {
          el.addEventListener("click", async () => {
            const leadId = el.getAttribute("data-reserve");
            const item = byLead.get(leadId);
            try {
              await reserveLead(item);
            } catch (error) {
              alert(error.message);
            }
          });
        });

        document.querySelectorAll("[data-release]").forEach((el) => {
          el.addEventListener("click", async () => {
            const leadId = el.getAttribute("data-release");
            const item = byLead.get(leadId);
            try {
              await releaseReservation(item);
            } catch (error) {
              alert(error.message);
            }
          });
        });

        document.querySelectorAll("[data-sell]").forEach((el) => {
          el.addEventListener("click", async () => {
            const leadId = el.getAttribute("data-sell");
            const item = byLead.get(leadId);
            try {
              await sellLead(item);
            } catch (error) {
              alert(error.message);
            }
          });
        });
      } catch (error) {
        tbody.innerHTML = `<tr><td colspan="9">${error.message}</td></tr>`;
      }
    }

    btn.addEventListener("click", load);
    load();
  }

  async function setupLeadDetail() {
    const id = qs("id");
    const pre = document.getElementById("lead-card-json");
    const meta = document.getElementById("lead-meta");
    const err = document.getElementById("lead-detail-error");
    if (!id) {
      err.textContent = "Falta id de lead.";
      return;
    }

    try {
      const data = await api(`/api/admin/leads/${id}`);
      if (meta) {
        const reserved = data.reserved_until ? new Date(data.reserved_until).toLocaleString() : "-";
        const soldAt = data.sold_at ? new Date(data.sold_at).toLocaleString() : "-";
        meta.textContent = `Estado comercial: ${data.commercial_state || "available"} | Reservado hasta: ${reserved} | Vendido en: ${soldAt}`;
      }
      pre.textContent = JSON.stringify(data, null, 2);
    } catch (error) {
      err.textContent = error.message;
    }
  }

  async function setupZones() {
    mountLogout();
    const tbody = document.getElementById("zones-tbody");
    const err = document.getElementById("zones-error");

    async function load() {
      err.textContent = "";
      try {
        const data = await api("/api/admin/zones");
        tbody.innerHTML = "";
        data.items.forEach((zone) => {
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td>${zone.zone_key}</td>
            <td>${zone.municipality}</td>
            <td><input type="number" step="1" data-base="${zone.id}" value="${zone.base_per_m2}" /></td>
            <td>
              <select data-demand="${zone.id}">
                <option value="alta" ${zone.demand_level === "alta" ? "selected" : ""}>alta</option>
                <option value="media" ${zone.demand_level === "media" ? "selected" : ""}>media</option>
                <option value="baja" ${zone.demand_level === "baja" ? "selected" : ""}>baja</option>
              </select>
            </td>
            <td><input type="checkbox" data-active="${zone.id}" ${zone.is_active ? "checked" : ""} /></td>
            <td><button class="button" data-save-zone="${zone.id}">Guardar</button></td>
          `;
          tbody.appendChild(tr);
        });

        document.querySelectorAll("[data-save-zone]").forEach((btn) => {
          btn.addEventListener("click", async () => {
            const id = btn.getAttribute("data-save-zone");
            const base = Number(document.querySelector(`[data-base='${id}']`).value);
            const demand = document.querySelector(`[data-demand='${id}']`).value;
            const active = document.querySelector(`[data-active='${id}']`).checked;
            await api(`/api/admin/zones/${id}`, {
              method: "PATCH",
              body: JSON.stringify({ base_per_m2: base, demand_level: demand, is_active: active }),
            });
            load();
          });
        });
      } catch (error) {
        err.textContent = error.message;
      }
    }

    load();
  }

  const page = document.body.dataset.page;
  if (page === "admin-login") setupLogin();
  if (page === "admin-leads") setupLeads();
  if (page === "admin-lead-detail") setupLeadDetail();
  if (page === "admin-zones") setupZones();
})();
