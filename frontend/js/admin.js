// ShieldGuard Admin & Owner Boshqaruv Moduli
window.AdminControl = {
  isOwner: false,
  isAdmin: false,
  activeMode: "user",

  init() {
    this.checkAdminStatus();

    // Rejimni o'zgartirish tugmalari
    const btnHeaderToggle = document.getElementById("btnHeaderRoleToggle");
    const btnAdminToggle = document.getElementById("btnAdminToggleRole");

    if (btnHeaderToggle) {
      btnHeaderToggle.addEventListener("click", () => this.toggleRoleMode());
    }
    if (btnAdminToggle) {
      btnAdminToggle.addEventListener("click", () => this.toggleRoleMode());
    }

    // Broadcast yuborish
    const btnBroadcast = document.getElementById("btnSendBroadcast");
    if (btnBroadcast) {
      btnBroadcast.addEventListener("click", () => this.sendBroadcast());
    }

    // Admin qo'shish
    const btnAddAdmin = document.getElementById("btnAddAdmin");
    if (btnAddAdmin) {
      btnAddAdmin.addEventListener("click", () => this.addAdmin());
    }

    // Firibgar karta qo'shish
    const btnAddCard = document.getElementById("btnAddScamCard");
    if (btnAddCard) {
      btnAddCard.addEventListener("click", () => this.addScamCard());
    }

    // Foydalanuvchilarni qidirish va yangilash
    const btnRefreshUsers = document.getElementById("btnRefreshAdminUsers");
    const inputSearch = document.getElementById("inputSearchUsers");
    if (btnRefreshUsers) {
      btnRefreshUsers.addEventListener("click", () => this.loadUsers(inputSearch.value));
    }
    if (inputSearch) {
      inputSearch.addEventListener("input", () => this.loadUsers(inputSearch.value));
    }
  },

  async checkAdminStatus() {
    const uid = window.ShieldGuard.currentUser.id;
    try {
      const resp = await fetch(`/api/admin/status/${uid}`);
      const data = await resp.json();

      this.isOwner = data.is_owner;
      this.isAdmin = data.is_admin;
      this.activeMode = data.active_mode;

      const roleBadge = document.getElementById("userRoleBadge");
      const btnHeaderToggle = document.getElementById("btnHeaderRoleToggle");
      const adminTabBtn = document.getElementById("adminTabBtn");

      if (this.isOwner) {
        btnHeaderToggle.classList.remove("hidden");
        if (this.activeMode === "owner") {
          roleBadge.textContent = "👑 OWNER";
          roleBadge.className = "text-[9px] px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 font-bold border border-amber-500/30";
          adminTabBtn.classList.remove("hidden");
          this.loadAdminMetrics();
          this.loadAdmins();
          this.loadCards();
          this.loadUsers();
        } else {
          roleBadge.textContent = "👤 USER (Sinov)";
          roleBadge.className = "text-[9px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 font-bold border border-slate-700";
          adminTabBtn.classList.add("hidden");
        }
      } else if (this.isAdmin) {
        roleBadge.textContent = "🛡️ ADMIN";
        roleBadge.className = "text-[9px] px-1.5 py-0.2 rounded bg-cyan-500/20 text-cyan-300 font-bold border border-cyan-500/30";
        adminTabBtn.classList.remove("hidden");
        this.loadAdminMetrics();
        this.loadCards();
        this.loadUsers();
      } else {
        roleBadge.textContent = "USER";
        adminTabBtn.classList.add("hidden");
      }
    } catch (e) {}
  },

  async toggleRoleMode() {
    const uid = window.ShieldGuard.currentUser.id;
    try {
      const resp = await fetch("/api/admin/toggle-mode", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ telegram_id: uid })
      });
      const data = await resp.json();
      alert(data.message);
      this.checkAdminStatus();
    } catch (e) {
      alert("Rejimni almashtirishda xatolik.");
    }
  },

  async loadAdminMetrics() {
    try {
      const resp = await fetch("/api/stats");
      const s = await resp.json();

      document.getElementById("statTotalUsers").textContent = s.total_scans ? `${Math.round(s.total_scans / 2)}` : "1";
      document.getElementById("statTotalScans").textContent = s.total_scans || "0";
      document.getElementById("statBlockedThreats").textContent = s.blocked_threats || "0";
      document.getElementById("statScamCards").textContent = s.total_blacklisted || "0";
    } catch (e) {}
  },

  async sendBroadcast() {
    const text = document.getElementById("broadcastInputText").value.trim();
    if (!text) {
      alert("Iltimos, e'lon matnini kiriting!");
      return;
    }

    if (!confirm("Haqiqatan ham ushbu xabarni botning barcha foydalanuvchilariga yubormoqchimisiz?")) {
      return;
    }

    const uid = window.ShieldGuard.currentUser.id;
    try {
      const resp = await fetch("/api/admin/broadcast", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ admin_telegram_id: uid, message: text })
      });
      const res = await resp.json();
      alert(`E'lon yuborildi!\nYetkazildi: ${res.sent_success} ta\nXato: ${res.sent_failed} ta`);
      document.getElementById("broadcastInputText").value = "";
    } catch (e) {
      alert("Xabar tarqatishda xatolik yuz berdi.");
    }
  },

  async loadAdmins() {
    const listEl = document.getElementById("currentAdminsList");
    const uid = window.ShieldGuard.currentUser.id;
    try {
      const resp = await fetch(`/api/admin/admins?caller_id=${uid}`);
      const admins = await resp.json();

      listEl.innerHTML = "";
      admins.forEach(a => {
        const item = document.createElement("div");
        item.className = "flex items-center justify-between p-2 rounded-lg bg-slate-950/60 border border-slate-800";
        item.innerHTML = `
          <div>
            <div class="font-bold text-slate-200">${a.full_name || 'Admin'} ${a.is_owner ? '👑 (Owner)' : '🛡️'}</div>
            <div class="text-[10px] text-slate-400">ID: ${a.telegram_id} ${a.username ? '(@' + a.username + ')' : ''}</div>
          </div>
          ${(!a.is_owner && this.isOwner) ? `<button onclick="window.AdminControl.removeAdmin(${a.telegram_id})" class="text-rose-400 text-xs px-2 py-0.5 rounded bg-rose-500/10 hover:bg-rose-500/20">O'chirish</button>` : ''}
        `;
        listEl.appendChild(item);
      });
    } catch (e) {}
  },

  async addAdmin() {
    const targetId = document.getElementById("inputNewAdminId").value.trim();
    if (!targetId) {
      alert("Telegram ID kiriting!");
      return;
    }

    const uid = window.ShieldGuard.currentUser.id;
    try {
      const resp = await fetch("/api/admin/add-admin", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ owner_telegram_id: uid, target_telegram_id: parseInt(targetId) })
      });
      const res = await resp.json();
      alert(res.message);
      document.getElementById("inputNewAdminId").value = "";
      this.loadAdmins();
    } catch (e) {
      alert("Admin tayinlashda xatolik.");
    }
  },

  async removeAdmin(targetId) {
    if (!confirm(`Haqiqatan ham ID ${targetId} adminini o'chirmoqchimisiz?`)) return;
    const uid = window.ShieldGuard.currentUser.id;
    try {
      const resp = await fetch("/api/admin/remove-admin", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ owner_telegram_id: uid, target_telegram_id: targetId })
      });
      const res = await resp.json();
      alert(res.message);
      this.loadAdmins();
    } catch (e) {
      alert("O'chirishda xatolik.");
    }
  },

  async loadCards() {
    const listEl = document.getElementById("adminCardsList");
    try {
      const resp = await fetch("/api/admin/card-blacklist");
      const cards = await resp.json();

      listEl.innerHTML = "";
      if (cards.length > 0) {
        cards.forEach(c => {
          const item = document.createElement("div");
          item.className = "flex items-center justify-between p-2 rounded-lg bg-slate-950/60 border border-slate-800";
          item.innerHTML = `
            <div class="truncate pr-2">
              <span class="font-bold text-rose-300 font-mono">${c.card_number}</span>
              <span class="text-[10px] text-slate-400 block truncate">${c.bank_name || ''} - ${c.reason}</span>
            </div>
            <button onclick="window.AdminControl.deleteCard(${c.id})" class="text-rose-400 text-xs px-2 py-0.5 rounded bg-rose-500/10">✕</button>
          `;
          listEl.appendChild(item);
        });
      } else {
        listEl.innerHTML = `<div class="text-slate-500 text-center py-2">Qora ro'yxatda kartalar yo'q.</div>`;
      }
    } catch (e) {}
  },

  async addScamCard() {
    const cardNum = document.getElementById("inputAdminCardNum").value.trim();
    const reason = document.getElementById("inputAdminCardReason").value.trim();
    if (!cardNum || !reason) {
      alert("Karta raqami va sababini kiriting!");
      return;
    }

    const uid = window.ShieldGuard.currentUser.id;
    try {
      const resp = await fetch("/api/admin/card-blacklist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          admin_telegram_id: uid,
          card_number: cardNum,
          reason: reason
        })
      });
      const res = await resp.json();
      alert(res.message);
      document.getElementById("inputAdminCardNum").value = "";
      document.getElementById("inputAdminCardReason").value = "";
      this.loadCards();
    } catch (e) {
      alert("Karta qo'shishda xatolik.");
    }
  },

  async deleteCard(cardId) {
    if (!confirm("Kartani ro'yxatdan o'chirmoqchimisiz?")) return;
    const uid = window.ShieldGuard.currentUser.id;
    try {
      await fetch(`/api/admin/card-blacklist/${cardId}?admin_id=${uid}`, { method: "DELETE" });
      this.loadCards();
    } catch (e) {
      alert("O'chirishda xatolik.");
    }
  },

  async loadUsers(query = "") {
    const listEl = document.getElementById("adminUsersList");
    const uid = window.ShieldGuard.currentUser.id;
    try {
      const url = query ? `/api/admin/users?caller_id=${uid}&query=${encodeURIComponent(query)}` : `/api/admin/users?caller_id=${uid}`;
      const resp = await fetch(url);
      const users = await resp.json();

      listEl.innerHTML = "";
      users.forEach(u => {
        const item = document.createElement("div");
        item.className = "flex items-center justify-between p-2 rounded-lg bg-slate-950/60 border border-slate-800";
        item.innerHTML = `
          <div>
            <div class="font-bold text-slate-200">${u.full_name || 'Foydalanuvchi'} ${u.role === 'owner' ? '👑' : (u.role === 'admin' ? '🛡️' : '')}</div>
            <div class="text-[10px] text-slate-400">ID: ${u.telegram_id} ${u.username ? '(@' + u.username + ')' : ''}</div>
          </div>
          ${u.role !== 'owner' ? `
            <button onclick="window.AdminControl.toggleBan(${u.telegram_id}, ${!u.is_banned})" class="text-xs px-2 py-0.5 rounded ${u.is_banned ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'}">
              ${u.is_banned ? 'Tiklash' : 'Bloklash'}
            </button>
          ` : ''}
        `;
        listEl.appendChild(item);
      });
    } catch (e) {}
  },

  async toggleBan(targetId, banStatus) {
    const uid = window.ShieldGuard.currentUser.id;
    try {
      const resp = await fetch("/api/admin/ban-user", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          admin_telegram_id: uid,
          target_telegram_id: targetId,
          ban: banStatus,
          reason: banStatus ? "Qoidabuzarlik" : "Tiklandi"
        })
      });
      const res = await resp.json();
      alert(res.message);
      this.loadUsers();
    } catch (e) {
      alert("Bloklash holatini o'zgartirib bo'lmadi.");
    }
  }
};

document.addEventListener("DOMContentLoaded", () => {
  window.AdminControl.init();
});
