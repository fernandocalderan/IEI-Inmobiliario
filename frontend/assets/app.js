(function () {
  const API_BASE = window.__API_BASE__ || window.API_BASE || "http://localhost:8000";

  function getSessionId() {
    let sid = localStorage.getItem("iei_session_id");
    if (!sid) {
      sid = (crypto && crypto.randomUUID) ? crypto.randomUUID() : String(Date.now());
      localStorage.setItem("iei_session_id", sid);
    }
    return sid;
  }

  async function trackEvent(eventName, payload = {}) {
    const sessionId = getSessionId();
    const leadId = localStorage.getItem("iei_last_lead_id") || undefined;
    try {
      await fetch(`${API_BASE}/api/events`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          event_name: eventName,
          event_version: "v1",
          session_id: sessionId,
          lead_id: leadId,
          payload,
        }),
      });
    } catch (_) {
      // no-op en MVP
    }
  }

  function money(n) {
    return new Intl.NumberFormat("es-ES", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(Number(n || 0));
  }

  function showError(message) {
    const el = document.getElementById("form-error");
    if (el) el.textContent = message;
  }

  function clearError() {
    const el = document.getElementById("form-error");
    if (el) el.textContent = "";
  }

  function buildLeadInput(formData) {
    return {
      property: {
        zone_key: String(formData.get("zone_key") || "").trim().toLowerCase(),
        municipality: String(formData.get("municipality") || "").trim(),
        neighborhood: String(formData.get("neighborhood") || "").trim() || null,
        postal_code: String(formData.get("postal_code") || "").trim() || null,
        property_type: formData.get("property_type"),
        m2: Number(formData.get("m2")),
        condition: formData.get("condition"),
        year_built: formData.get("year_built") ? Number(formData.get("year_built")) : null,
        has_elevator: formData.get("has_elevator") === "on",
        has_terrace: formData.get("has_terrace") === "on",
        terrace_m2: formData.get("terrace_m2") ? Number(formData.get("terrace_m2")) : null,
        has_parking: formData.get("has_parking") === "on",
        has_views: formData.get("has_views") === "on",
      },
      owner: {
        sale_horizon: formData.get("sale_horizon"),
        motivation: formData.get("motivation"),
        already_listed: formData.get("already_listed"),
        exclusivity: formData.get("exclusivity"),
        expected_price: formData.get("expected_price") ? Number(formData.get("expected_price")) : null,
      },
    };
  }

  async function submitWizard(formEl) {
    const fd = new FormData(formEl);
    const leadInput = buildLeadInput(fd);

    if (leadInput.property.m2 <= 0) {
      showError("m2 debe ser mayor que 0.");
      return;
    }

    clearError();

    const scoreResp = await fetch(`${API_BASE}/api/iei/score`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Session-ID": getSessionId() },
      body: JSON.stringify(leadInput),
    });

    const scoreData = await scoreResp.json();

    if (!scoreResp.ok) {
      if (scoreResp.status === 422 && scoreData?.error?.code === "ZONE_NOT_CONFIGURED") {
        showError("Todavía no tenemos datos suficientes para esta zona. Déjanos tu contacto y te avisamos cuando esté disponible.");
      } else {
        showError(scoreData?.error?.message || "No se pudo calcular el score.");
      }
      return;
    }

    const leadPayload = {
      lead: {
        owner_name: String(fd.get("owner_name") || "").trim(),
        owner_email: String(fd.get("owner_email") || "").trim(),
        owner_phone: String(fd.get("owner_phone") || "").trim(),
        consent_contact: fd.get("consent_contact") === "on",
        consent_text_version: "v1",
        source_campaign: String(fd.get("source_campaign") || "").trim() || null,
        utm_source: null,
        utm_medium: null,
        utm_campaign: null,
        utm_term: null,
        utm_content: null,
      },
      input: leadInput,
      company_website: String(fd.get("company_website") || "").trim() || null,
    };

    const leadResp = await fetch(`${API_BASE}/api/leads`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Session-ID": getSessionId() },
      body: JSON.stringify(leadPayload),
    });

    const leadData = await leadResp.json();
    if (!leadResp.ok) {
      showError(leadData?.error?.message || "No se pudo crear el lead.");
      return;
    }

    localStorage.setItem("iei_last_result", JSON.stringify(scoreData));
    localStorage.setItem("iei_last_lead", JSON.stringify(leadData));
    const leadId = leadData.lead_id || leadData.existing_lead_id;
    if (leadId) {
      localStorage.setItem("iei_last_lead_id", leadId);
    }

    await trackEvent("submit_lead", {
      zone_key: leadInput.property.zone_key,
      sale_horizon: leadInput.owner.sale_horizon,
      motivation: leadInput.owner.motivation,
      expected_price_present: leadInput.owner.expected_price != null,
      duplicate: leadData.duplicate === true,
    });

    window.location.href = "result.html";
  }

  function setupLanding() {
    trackEvent("view_landing", { source_campaign: null });
    const cta = document.getElementById("cta-start");
    if (cta) {
      cta.addEventListener("click", () => trackEvent("start_form", {}));
    }
  }

  function setupForm() {
    const form = document.getElementById("iei-form");
    if (!form) return;

    let currentStep = 1;
    const totalSteps = 4;
    let started = false;

    const steps = Array.from(document.querySelectorAll(".step"));
    const nextBtn = document.getElementById("next-step");
    const prevBtn = document.getElementById("prev-step");
    const submitBtn = document.getElementById("submit-form");

    function renderStep() {
      steps.forEach((el) => {
        const step = Number(el.dataset.step);
        el.classList.toggle("active", step === currentStep);
      });
      prevBtn.style.visibility = currentStep === 1 ? "hidden" : "visible";
      nextBtn.style.display = currentStep === totalSteps ? "none" : "inline-block";
      submitBtn.style.display = currentStep === totalSteps ? "inline-block" : "none";
    }

    form.addEventListener("input", () => {
      if (!started) {
        started = true;
        trackEvent("start_form", {});
      }
    });

    nextBtn.addEventListener("click", async () => {
      await trackEvent("step_complete", { step_name: currentStep });
      currentStep = Math.min(totalSteps, currentStep + 1);
      renderStep();
    });

    prevBtn.addEventListener("click", () => {
      currentStep = Math.max(1, currentStep - 1);
      renderStep();
    });

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      await submitWizard(form);
    });

    renderStep();
  }

  function setupResult() {
    const resultStr = localStorage.getItem("iei_last_result");
    if (!resultStr) {
      const err = document.getElementById("result-error");
      err.style.display = "block";
      err.textContent = "No hay resultado para mostrar.";
      return;
    }

    const data = JSON.parse(resultStr);
    const card = document.getElementById("result-card");
    card.style.display = "block";

    document.getElementById("kpi-score").textContent = data.iei_score;
    document.getElementById("kpi-tier").textContent = data.tier;
    document.getElementById("kpi-center").textContent = money(data.price_estimate.adjusted_price);
    document.getElementById("range").textContent = `${money(data.price_estimate.range_low)} - ${money(data.price_estimate.range_high)}`;
    document.getElementById("pricing-note").textContent = data.pricing_alignment.note;
    document.getElementById("recommendation").textContent = data.recommendation;

    trackEvent("view_result", {
      iei_score: data.iei_score,
      tier: data.tier,
      gap_percent: data.pricing_alignment.gap_percent,
      zone_key: data?.zone?.zone_key || null,
    });

    const btn = document.getElementById("call-requested");
    if (btn) {
      btn.addEventListener("click", async () => {
        await trackEvent("call_requested", { tier: data.tier });
        btn.textContent = "Solicitud enviada";
        btn.disabled = true;
      });
    }
  }

  const page = document.body.dataset.page;
  if (page === "landing") setupLanding();
  if (page === "form") setupForm();
  if (page === "result") setupResult();
})();
