// Shartnoma Rentgeni (Legal X-Ray) Moduli
window.LegalModule = {
  selectedContractFile: null,

  init() {
    const dropzone = document.getElementById("contractDropzone");
    const fileInput = document.getElementById("contractFileInput");
    const btnRemove = document.getElementById("btnRemoveContract");
    const btnScan = document.getElementById("btnScanContract");

    dropzone.addEventListener("click", () => fileInput.click());
    dropzone.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropzone.classList.add("dragover");
    });
    dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
    dropzone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
      if (e.dataTransfer.files.length > 0) {
        this.handleContractSelected(e.dataTransfer.files[0]);
      }
    });

    fileInput.addEventListener("change", (e) => {
      if (e.target.files.length > 0) {
        this.handleContractSelected(e.target.files[0]);
      }
    });

    btnRemove.addEventListener("click", () => {
      this.selectedContractFile = null;
      document.getElementById("selectedContractInfo").classList.add("hidden");
      dropzone.classList.remove("hidden");
      fileInput.value = "";
    });

    btnScan.addEventListener("click", () => this.scanContract());
  },

  handleContractSelected(file) {
    this.selectedContractFile = file;
    document.getElementById("selectedContractName").textContent = `${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;
    document.getElementById("selectedContractInfo").classList.remove("hidden");
    document.getElementById("contractDropzone").classList.add("hidden");
  },

  async scanContract() {
    const rawText = document.getElementById("contractRawText").value.trim();
    if (!this.selectedContractFile && !rawText) {
      alert("Iltimos, shartnoma faylini yuklang yoki matnini kiriting!");
      return;
    }

    const btn = document.getElementById("btnScanContract");
    this.setLoading(btn, true);

    const formData = new FormData();
    if (this.selectedContractFile) {
      formData.append("file", this.selectedContractFile);
    }
    if (rawText) {
      formData.append("raw_text", rawText);
    }
    formData.append("telegram_id", window.ShieldGuard.currentUser.id);

    try {
      const response = await fetch("/api/scan/contract", {
        method: "POST",
        body: formData
      });

      const data = await response.json();
      this.renderLegalResult(data);
    } catch (e) {
      alert("Shartnomani tahlil qilishda xatolik yuz berdi.");
    } finally {
      this.setLoading(btn, false);
    }
  },

  renderLegalResult(data) {
    const card = document.getElementById("legalResultCard");
    card.classList.remove("hidden");
    card.scrollIntoView({ behavior: "smooth" });

    document.getElementById("legalContractType").textContent = data.contract_type || "Shartnoma";
    const score = data.overall_safety_score || 70;
    const scoreBadge = document.getElementById("legalScoreBadge");
    scoreBadge.textContent = `${score}/100`;

    if (score < 50) {
      scoreBadge.className = "text-lg font-black text-rose-500";
    } else if (score < 75) {
      scoreBadge.className = "text-lg font-black text-amber-400";
    } else {
      scoreBadge.className = "text-lg font-black text-emerald-400";
    }

    document.getElementById("legalSummaryText").textContent = data.summary_uz || "Audit yakunlandi.";

    // Qizil bayroqlar (Tuzoqlar)
    const dangerousClausesContainer = document.getElementById("legalDangerousClauses");
    dangerousClausesContainer.innerHTML = "";
    if (data.dangerous_clauses && data.dangerous_clauses.length > 0) {
      data.dangerous_clauses.forEach(clause => {
        const item = document.createElement("div");
        item.className = "bg-rose-950/30 border border-rose-800/40 p-2.5 rounded-xl text-xs";
        item.innerHTML = `
          <div class="flex items-center justify-between font-bold text-rose-300 mb-1">
            <span>⚠️ ${clause.clause_num || 'Band'}</span>
            <span class="text-[10px] uppercase px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-400 font-bold">${clause.severity || 'xavfli'}</span>
          </div>
          <div class="text-slate-300 mb-1.5">${clause.explanation_uz}</div>
          ${clause.original_quote ? `<div class="text-[10px] text-slate-400 italic bg-black/30 p-1.5 rounded">"${clause.original_quote}"</div>` : ''}
        `;
        dangerousClausesContainer.appendChild(item);
      });
    }

    // Moliyaviy xavflar
    const finContainer = document.getElementById("legalFinancialTraps");
    finContainer.innerHTML = "";
    if (data.financial_traps && data.financial_traps.length > 0) {
      data.financial_traps.forEach(trap => {
        const item = document.createElement("div");
        item.className = "bg-amber-950/30 border-l-2 border-amber-500 p-2 rounded-r-lg text-xs text-amber-200";
        item.textContent = trap;
        finContainer.appendChild(item);
      });
    }

    // Tavsiyalar
    const recContainer = document.getElementById("legalRecommendations");
    recContainer.innerHTML = "";
    if (data.recommendations && data.recommendations.length > 0) {
      data.recommendations.forEach(rec => {
        const item = document.createElement("div");
        item.className = "flex items-start gap-1.5 mb-1";
        item.innerHTML = `<span class="text-emerald-400 font-bold">✓</span> <span>${rec}</span>`;
        recContainer.appendChild(item);
      });
    }
  },

  setLoading(btn, isLoading) {
    const textEl = btn.querySelector(".btn-text");
    const loaderEl = btn.querySelector(".btn-loader");
    btn.disabled = isLoading;
    if (isLoading) {
      textEl.classList.add("hidden");
      loaderEl.classList.remove("hidden");
    } else {
      textEl.classList.remove("hidden");
      loaderEl.classList.add("hidden");
    }
  }
};

document.addEventListener("DOMContentLoaded", () => {
  window.LegalModule.init();
});
