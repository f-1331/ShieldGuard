// ShieldGuard Mini App - Asosiy boshqaruv kodi
window.ShieldGuard = {
  currentUser: {
    id: 100000001, // Standart sinov ID
    firstName: "Foydalanuvchi",
    username: ""
  },
  activeTab: "tabScanner",

  init() {
    // 1. Telegram WebApp integratsiyasi
    if (window.Telegram && window.Telegram.WebApp) {
      const tg = window.Telegram.WebApp;
      tg.ready();
      tg.expand();

      if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
        const u = tg.initDataUnsafe.user;
        this.currentUser.id = u.id;
        this.currentUser.firstName = u.first_name || "Foydalanuvchi";
        this.currentUser.username = u.username || "";

        const nameEl = document.getElementById("userName");
        if (nameEl) {
          nameEl.textContent = this.currentUser.firstName;
        }
      }
    }

    // 2. Tablarni almashtirish
    this.initTabs();
  },

  initTabs() {
    const tabBtns = document.querySelectorAll(".tab-btn");
    const tabPanes = document.querySelectorAll(".tab-pane");

    tabBtns.forEach(btn => {
      btn.addEventListener("click", () => {
        const targetTab = btn.getAttribute("data-tab");
        
        tabBtns.forEach(b => b.classList.remove("active"));
        tabPanes.forEach(p => p.classList.remove("active"));

        btn.classList.add("active");
        const activePane = document.getElementById(targetTab);
        if (activePane) {
          activePane.classList.add("active");
        }

        this.activeTab = targetTab;

        // Agar Oila bo'limi ochilsa, tarixni avtomatik yangilash
        if (targetTab === "tabFamily" && window.FamilyShield) {
          window.FamilyShield.loadFamilyData();
          window.FamilyShield.loadHistory();
          window.FamilyShield.loadBlacklist();
        }
      });
    });
  },

  showToast(message, type = "info") {
    // Telegram haptic feedback
    if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.HapticFeedback) {
      if (type === "error") {
        window.Telegram.WebApp.HapticFeedback.notificationOccurred("error");
      } else {
        window.Telegram.WebApp.HapticFeedback.notificationOccurred("success");
      }
    }
    alert(message);
  }
};

document.addEventListener("DOMContentLoaded", () => {
  window.ShieldGuard.init();
});
