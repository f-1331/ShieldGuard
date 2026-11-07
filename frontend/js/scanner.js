// Skaner va Kiber-himoya moduli
window.ScannerModule = {
  selectedFile: null,

  init() {
    // Rejim tugmalari (Havola vs Fayl)
    const modeUrlBtn = document.getElementById("modeUrlBtn");
    const modeFileBtn = document.getElementById("modeFileBtn");
    const urlSection = document.getElementById("urlScanSection");
    const fileSection = document.getElementById("fileScanSection");

    modeUrlBtn.addEventListener("click", () => {
      modeUrlBtn.className = "flex-1 py-2 rounded-lg font-bold bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 transition-all";
      modeFileBtn.className = "flex-1 py-2 rounded-lg font-bold text-slate-400 hover:text-slate-200 transition-all";
      urlSection.classList.remove("hidden");
      fileSection.classList.add("hidden");
    });

    modeFileBtn.addEventListener("click", () => {
      modeFileBtn.className = "flex-1 py-2 rounded-lg font-bold bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 transition-all";
      modeUrlBtn.className = "flex-1 py-2 rounded-lg font-bold text-slate-400 hover:text-slate-200 transition-all";
      fileSection.classList.remove("hidden");
      urlSection.classList.add("hidden");
    });

    // URL tekshirish
    const btnScanUrl = document.getElementById("btnScanUrl");
    btnScanUrl.addEventListener("click", () => this.scanUrlOrText());

    // Fayl tanlash
    const dropzone = document.getElementById("fileDropzone");
    const fileInput = document.getElementById("fileInput");
    const btnScanFile = document.getElementById("btnScanFile");
    const btnRemoveFile = document.getElementById("btnRemoveFile");

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
        this.handleFileSelected(e.dataTransfer.files[0]);
      }
    });

    fileInput.addEventListener("change", (e) => {
      if (e.target.files.length > 0) {
        this.handleFileSelected(e.target.files[0]);
      }
    });

    btnRemoveFile.addEventListener("click", () => {
      this.selectedFile = null;
      document.getElementById("selectedFileInfo").classList.add("hidden");
      dropzone.classList.remove("hidden");
      btnScanFile.disabled = true;
      fileInput.value = "";
    });

    btnScanFile.addEventListener("click", () => this.scanFile());
  },

  handleFileSelected(file) {
    this.selectedFile = file;
    document.getElementById("selectedFileName").textContent = `${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;
    document.getElementById("selectedFileInfo").classList.remove("hidden");
    document.getElementById("fileDropzone").classList.add("hidden");
    document.getElementById("btnScanFile").disabled = false;
  },

  async scanUrlOrText() {
    const text = document.getElementById("scanInputText").value.trim();
    if (!text) {
      alert("Iltimos, tekshirish uchun havola yoki matn kiriting!");
      return;
    }

    const btn = document.getElementById("btnScanUrl");
    this.setLoading(btn, true);

    try {
      const response = await fetch("/api/scan/url-or-text", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: text,
          telegram_id: window.ShieldGuard.currentUser.id
        })
      });

      const data = await response.json();
      this.renderScanResult(data);
    } catch (e) {
      alert("Tekshiruv vaqtida tarmoq xatosi yuz berdi.");
    } finally {
      this.setLoading(btn, false);
    }
  },

  async scanFile() {
    if (!this.selectedFile) return;

    const btn = document.getElementById("btnScanFile");
    this.setLoading(btn, true);

    const formData = new FormData();
    formData.append("file", this.selectedFile);
    formData.append("telegram_id", window.ShieldGuard.currentUser.id);

    try {
      const response = await fetch("/api/scan/file", {
        method: "POST",
        body: formData
      });

      const data = await response.json();
      this.renderScanResult(data);
    } catch (e) {
      alert("Faylni yuklashda xatolik yuz berdi.");
    } finally {
      this.setLoading(btn, false);
    }
  },

  renderScanResult(data) {
    const card = document.getElementById("scanResultCard");
    card.classList.remove("hidden");
    card.scrollIntoView({ behavior: "smooth" });

    const riskScore = Math.round(data.risk_score || 0);
    const gaugePath = document.getElementById("gaugePath");
    const gaugeScore = document.getElementById("gaugeScore");
    const gaugeVerdictText = document.getElementById("gaugeVerdictText");
    const verdictBadge = document.getElementById("resultVerdictBadge");

    // Gauge hisoblash: SVG radius 35 bo'lsa yarim aylanasi uzunligi ~110
    const maxOffset = 110;
    const offset = maxOffset - (riskScore / 100) * maxOffset;
    gaugePath.style.strokeDashoffset = offset;
    gaugeScore.textContent = `${riskScore}%`;

    // Ranglarni sozlash
    gaugePath.className.baseVal = "gauge-fill";
    if (riskScore >= 70) {
      gaugePath.classList.add("dangerous");
      gaugeScore.className = "gauge-value text-rose-500";
      gaugeVerdictText.className = "gauge-label text-rose-500";
      gaugeVerdictText.textContent = "Kritik Xavfli!";
      verdictBadge.className = "badge-pill badge-dangerous";
      verdictBadge.textContent = "🔴 Xavfli!";
    } else if (riskScore >= 40) {
      gaugePath.classList.add("suspicious");
      gaugeScore.className = "gauge-value text-amber-400";
      gaugeVerdictText.className = "gauge-label text-amber-400";
      gaugeVerdictText.textContent = "Shubhali";
      verdictBadge.className = "badge-pill badge-suspicious";
      verdictBadge.textContent = "🟡 Shubhali";
    } else {
      gaugePath.classList.add("safe");
      gaugeScore.className = "gauge-value text-emerald-400";
      gaugeVerdictText.className = "gauge-label text-emerald-400";
      gaugeVerdictText.textContent = "Xavfsiz";
      verdictBadge.className = "badge-pill badge-safe";
      verdictBadge.textContent = "🟢 Xavfsiz";
    }

    // Xulosa matni
    document.getElementById("resultSummaryText").textContent = data.summary_uz || "Tahlil yakunlandi.";

    // Qizil bayroqlar
    const redFlagsContainer = document.getElementById("redFlagsContainer");
    const redFlagsList = document.getElementById("redFlagsList");
    redFlagsList.innerHTML = "";
    if (data.red_flags && data.red_flags.length > 0) {
      redFlagsContainer.classList.remove("hidden");
      data.red_flags.forEach(flag => {
        const item = document.createElement("div");
        item.className = "red-flag-item";
        item.textContent = flag;
        redFlagsList.appendChild(item);
      });
    } else {
      redFlagsContainer.classList.add("hidden");
    }

    // APK Ruxsatlari
    const apkContainer = document.getElementById("apkPermissionsContainer");
    const apkList = document.getElementById("apkPermissionsList");
    apkList.innerHTML = "";
    if (data.dangerous_permissions && data.dangerous_permissions.length > 0) {
      apkContainer.classList.remove("hidden");
      data.dangerous_permissions.forEach(perm => {
        const pEl = document.createElement("div");
        pEl.className = "bg-rose-950/40 border border-rose-800/40 p-2 rounded-lg text-xs";
        pEl.innerHTML = `
          <div class="font-bold text-rose-300">${perm.name_uz}</div>
          <div class="text-[11px] text-slate-400">${perm.risk_uz}</div>
        `;
        apkList.appendChild(pEl);
      });
    } else {
      apkContainer.classList.add("hidden");
    }

    // Ijobiy tekshiruvlar
    const posContainer = document.getElementById("positiveFlagsContainer");
    const posList = document.getElementById("positiveFlagsList");
    posList.innerHTML = "";
    if (data.positive_flags && data.positive_flags.length > 0) {
      posContainer.classList.remove("hidden");
      data.positive_flags.forEach(f => {
        const pItem = document.createElement("div");
        pItem.className = "positive-flag-item";
        pItem.textContent = f;
        posList.appendChild(pItem);
      });
    } else {
      posContainer.classList.add("hidden");
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
  window.ScannerModule.init();
});
