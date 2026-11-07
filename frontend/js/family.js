// Oila Qalqoni, Tarix va Qora Ro'yxat Moduli
window.FamilyShield = {
  init() {
    // Yaqin insonni ulash tugmasi
    const btnLink = document.getElementById("btnLinkFamily");
    btnLink.addEventListener("click", () => this.linkFamilyMember());

    // Tarixni yangilash
    const btnRefreshHistory = document.getElementById("btnRefreshHistory");
    btnRefreshHistory.addEventListener("click", () => this.loadHistory());

    // Qora ro'yxatga hisobot berish modal oynasi
    const btnOpenReport = document.getElementById("btnOpenReportModal");
    const btnCloseModal = document.getElementById("btnCloseModal");
    const modal = document.getElementById("reportModal");
    const btnSubmit = document.getElementById("btnSubmitReport");

    btnOpenReport.addEventListener("click", () => modal.classList.remove("hidden"));
    btnCloseModal.addEventListener("click", () => modal.classList.add("hidden"));
    btnSubmit.addEventListener("click", () => this.submitScamReport());

    // Dastlabki yuklash
    this.loadFamilyData();
    this.loadHistory();
    this.loadBlacklist();
  },

  async linkFamilyMember() {
    const parentId = document.getElementById("familyParentId").value.trim();
    const relation = document.getElementById("familyRelationName").value.trim() || "Yaqin insonim";

    if (!parentId) {
      alert("Iltimos, yaqiningizning Telegram ID raqamini kiriting!");
      return;
    }

    try {
      const resp = await fetch("/api/family/link", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          parent_telegram_id: parseInt(parentId),
          child_telegram_id: window.ShieldGuard.currentUser.id,
          relationship_name: relation
        })
      });

      const res = await resp.json();
      alert(res.message);
      document.getElementById("familyParentId").value = "";
      document.getElementById("familyRelationName").value = "";
      this.loadFamilyData();
    } catch (e) {
      alert("Himoyaga ulashda xatolik yuz berdi.");
    }
  },

  async loadFamilyData() {
    const listEl = document.getElementById("familyList");
    try {
      const resp = await fetch(`/api/family/${window.ShieldGuard.currentUser.id}`);
      const data = await resp.json();

      listEl.innerHTML = "";
      if (data.protecting && data.protecting.length > 0) {
        data.protecting.forEach(m => {
          const item = document.createElement("div");
          item.className = "flex items-center justify-between p-2.5 rounded-xl bg-slate-900/60 border border-slate-800";
          item.innerHTML = `
            <div>
              <div class="font-bold text-slate-200">🛡️ ${m.relationship_name}</div>
              <div class="text-[10px] text-slate-400">ID: ${m.relative_telegram_id} | ${m.created_at}</div>
            </div>
            <button onclick="window.FamilyShield.removeFamilyLink(${m.link_id})" class="text-rose-400 text-xs px-2 py-1 rounded bg-rose-500/10 hover:bg-rose-500/20">
              O'chirish
            </button>
          `;
          listEl.appendChild(item);
        });
      } else {
        listEl.innerHTML = `<div class="text-slate-500 text-center py-2">Hozircha siz hech kimni himoyaga ulamadingiz.</div>`;
      }
    } catch (e) {
      listEl.innerHTML = `<div class="text-slate-500 text-center py-2">Ma'lumotlarni yuklab bo'lmadi.</div>`;
    }
  },

  async removeFamilyLink(linkId) {
    if (!confirm("Haqiqatan ham ushbu himoyani bekor qilmoqchimisiz?")) return;
    try {
      await fetch(`/api/family/link/${linkId}`, { method: "DELETE" });
      this.loadFamilyData();
    } catch (e) {
      alert("O'chirishda xatolik.");
    }
  },

  async loadHistory() {
    const listEl = document.getElementById("historyList");
    try {
      const resp = await fetch(`/api/history/${window.ShieldGuard.currentUser.id}`);
      const items = await resp.json();

      listEl.innerHTML = "";
      if (items.length > 0) {
        items.forEach(h => {
          const item = document.createElement("div");
          item.className = "timeline-item";

          let badgeClass = "badge-safe";
          let badgeText = "Xavfsiz";
          if (h.risk_score >= 70) {
            badgeClass = "badge-dangerous";
            badgeText = "Xavfli";
          } else if (h.risk_score >= 40) {
            badgeClass = "badge-suspicious";
            badgeText = "Shubhali";
          }

          item.innerHTML = `
            <div class="flex-1 pr-2">
              <div class="font-bold text-slate-200 truncate max-w-[200px]">${h.target_name}</div>
              <div class="text-[10px] text-slate-400">${h.created_at} • ${h.scan_type}</div>
              <div class="text-[11px] text-slate-300 mt-1 line-clamp-1">${h.summary_uz}</div>
            </div>
            <div class="text-right">
              <span class="badge-pill ${badgeClass}">${badgeText}</span>
              <div class="text-[10px] text-slate-400 mt-1 font-bold">${Math.round(h.risk_score)}%</div>
            </div>
          `;
          listEl.appendChild(item);
        });
      } else {
        listEl.innerHTML = `<div class="text-slate-500 text-center py-3">Hozircha hech qanday tekshiruv o'tkazilmadi.</div>`;
      }
    } catch (e) {
      listEl.innerHTML = `<div class="text-slate-500 text-center py-3">Tarixni yuklab bo'lmadi.</div>`;
    }
  },

  async loadBlacklist() {
    const listEl = document.getElementById("communityBlacklist");
    try {
      const resp = await fetch("/api/community/blacklist");
      const list = await resp.json();

      listEl.innerHTML = "";
      if (list.length > 0) {
        list.forEach(b => {
          const item = document.createElement("div");
          item.className = "p-2.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs";
          item.innerHTML = `
            <div class="flex items-center justify-between mb-1">
              <span class="font-bold text-rose-400">${b.domain_or_pattern}</span>
              <span class="text-[9px] uppercase px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300">${b.category}</span>
            </div>
            <div class="text-[11px] text-slate-300 leading-tight">${b.reason}</div>
          `;
          listEl.appendChild(item);
        });
      }
    } catch (e) {
      listEl.innerHTML = `<div class="text-slate-500 text-center py-2">Qora ro'yxatni yuklab bo'lmadi.</div>`;
    }
  },

  async submitScamReport() {
    const domain = document.getElementById("reportDomain").value.trim();
    const category = document.getElementById("reportCategory").value;
    const reason = document.getElementById("reportReason").value.trim();

    if (!domain || !reason) {
      alert("Iltimos, manzil va uning nima sababdan xavfli ekanini yozing!");
      return;
    }

    try {
      const resp = await fetch("/api/community/report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          domain_or_pattern: domain,
          category: category,
          reason: reason,
          reported_by_telegram_id: window.ShieldGuard.currentUser.id
        })
      });

      const res = await resp.json();
      alert(res.message);
      document.getElementById("reportModal").classList.add("hidden");
      document.getElementById("reportDomain").value = "";
      document.getElementById("reportReason").value = "";
      this.loadBlacklist();
    } catch (e) {
      alert("Xabar yuborishda xatolik yuz berdi.");
    }
  }
};

document.addEventListener("DOMContentLoaded", () => {
  window.FamilyShield.init();
});
