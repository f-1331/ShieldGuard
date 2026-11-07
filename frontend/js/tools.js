// Xavfsizlik asboblari: Karta, Bot, SOS va Kiber-Test
window.SecurityTools = {
  currentQuizQuestions: [],
  userAnswers: {},

  init() {
    // Sub-tools tab buttons
    const toolBtnCard = document.getElementById("toolBtnCard");
    const toolBtnBot = document.getElementById("toolBtnBot");
    const toolBtnSos = document.getElementById("toolBtnSos");
    const toolBtnQuiz = document.getElementById("toolBtnQuiz");

    const secCard = document.getElementById("toolSectionCard");
    const secBot = document.getElementById("toolSectionBot");
    const secSos = document.getElementById("toolSectionSos");
    const secQuiz = document.getElementById("toolSectionQuiz");

    const setToolActive = (activeBtn, activeSec) => {
      [toolBtnCard, toolBtnBot, toolBtnSos, toolBtnQuiz].forEach(b => {
        b.className = "py-2 rounded-lg text-slate-400 hover:text-slate-200";
      });
      [secCard, secBot, secSos, secQuiz].forEach(s => s.classList.add("hidden"));

      activeBtn.className = "py-2 rounded-lg bg-cyan-500/20 text-cyan-400 border border-cyan-500/30";
      activeSec.classList.remove("hidden");
    };

    toolBtnCard.addEventListener("click", () => setToolActive(toolBtnCard, secCard));
    toolBtnBot.addEventListener("click", () => setToolActive(toolBtnBot, secBot));
    toolBtnSos.addEventListener("click", () => {
      setToolActive(toolBtnSos, secSos);
      this.loadEmergencyGuide();
    });
    toolBtnQuiz.addEventListener("click", () => {
      setToolActive(toolBtnQuiz, secQuiz);
      this.loadQuiz();
    });

    // Karta tekshirish
    const btnCheckCard = document.getElementById("btnCheckCard");
    btnCheckCard.addEventListener("click", () => this.checkCard());

    // Bot tekshirish
    const btnCheckBot = document.getElementById("btnCheckBot");
    btnCheckBot.addEventListener("click", () => this.checkBot());

    // Quiz qayta topshirish
    const btnRetry = document.getElementById("btnRetryQuiz");
    if (btnRetry) {
      btnRetry.addEventListener("click", () => this.loadQuiz());
    }
  },

  async checkCard() {
    const cardInput = document.getElementById("inputCardNumber").value.trim();
    if (!cardInput) {
      alert("Iltimos, 16 talik karta raqamini kiriting!");
      return;
    }

    try {
      const resp = await fetch("/api/tools/check-card", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ card_number: cardInput })
      });
      const data = await resp.json();

      const box = document.getElementById("cardResultBox");
      box.classList.remove("hidden");

      document.getElementById("cardMasked").textContent = data.card_number_masked || cardInput;
      document.getElementById("cardSystem").textContent = data.payment_system || "Noma'lum";
      document.getElementById("cardBank").textContent = data.bank_name || "Noma'lum";
      document.getElementById("cardType").textContent = data.card_type || "Standart";

      const luhnEl = document.getElementById("cardLuhn");
      if (data.is_luhn_valid) {
        luhnEl.className = "text-emerald-400 font-semibold";
        luhnEl.textContent = "To'g'ri (Haqiqiy karta)";
      } else {
        luhnEl.className = "text-rose-400 font-semibold";
        luhnEl.textContent = "Noto'g'ri (Qalbaki tuzilma)";
      }

      const badge = document.getElementById("cardVerdictBadge");
      const warningsList = document.getElementById("cardWarningsList");
      warningsList.innerHTML = "";

      if (data.is_in_blacklist || data.risk_score >= 70) {
        badge.className = "badge-pill badge-dangerous";
        badge.textContent = "🔴 Firibgar Karta!";
      } else if (data.risk_score >= 40) {
        badge.className = "badge-pill badge-suspicious";
        badge.textContent = "🟡 Shubhali";
      } else {
        badge.className = "badge-pill badge-safe";
        badge.textContent = "🟢 Xavfsiz Karta";
      }

      if (data.warnings && data.warnings.length > 0) {
        data.warnings.forEach(w => {
          const item = document.createElement("div");
          item.className = "p-2 rounded-lg bg-rose-950/40 border border-rose-800/40 text-[11px] text-rose-300";
          item.textContent = w;
          warningsList.appendChild(item);
        });
      }
    } catch (e) {
      alert("Karta tekshiruvida xatolik yuz berdi.");
    }
  },

  async checkBot() {
    const botInput = document.getElementById("inputBotUsername").value.trim();
    if (!botInput) {
      alert("Iltimos, bot username'ini kiriting!");
      return;
    }

    try {
      const resp = await fetch("/api/tools/check-bot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: botInput })
      });
      const data = await resp.json();

      const box = document.getElementById("botResultBox");
      box.classList.remove("hidden");

      document.getElementById("botTargetName").textContent = data.target;
      document.getElementById("botSummaryText").textContent = data.summary_uz;

      const badge = document.getElementById("botVerdictBadge");
      if (data.risk_score >= 70) {
        badge.className = "badge-pill badge-dangerous";
        badge.textContent = "🔴 Xavfli Bot";
      } else if (data.risk_score >= 40) {
        badge.className = "badge-pill badge-suspicious";
        badge.textContent = "🟡 Shubhali";
      } else {
        badge.className = "badge-pill badge-safe";
        badge.textContent = "🟢 Rasmiy / Xavfsiz";
      }

      const flagsList = document.getElementById("botFlagsList");
      flagsList.innerHTML = "";
      if (data.flags && data.flags.length > 0) {
        data.flags.forEach(f => {
          const item = document.createElement("div");
          item.className = "p-1.5 rounded bg-rose-950/30 text-[11px] text-rose-300";
          item.textContent = f;
          flagsList.appendChild(item);
        });
      }
    } catch (e) {
      alert("Botni tekshirishda xatolik yuz berdi.");
    }
  },

  async loadEmergencyGuide() {
    const listEl = document.getElementById("emergencyBanksList");
    try {
      const resp = await fetch("/api/tools/emergency-guide");
      const data = await resp.json();

      listEl.innerHTML = "";
      data.banks_contacts.forEach(b => {
        const item = document.createElement("a");
        item.href = `tel:${b.phone.replace(/\s+/g, '')}`;
        item.className = "bg-slate-900/80 p-2 rounded-xl border border-slate-800 hover:border-cyan-500/40 flex items-center justify-between transition";
        item.innerHTML = `
          <span class="text-slate-200 font-semibold truncate pr-1">${b.name}</span>
          <span class="text-cyan-400 font-bold font-mono">${b.short}</span>
        `;
        listEl.appendChild(item);
      });
    } catch (e) {}
  },

  async loadQuiz() {
    const container = document.getElementById("quizContainer");
    const resultBox = document.getElementById("quizResultBox");
    resultBox.classList.add("hidden");
    this.userAnswers = {};

    try {
      const resp = await fetch("/api/tools/quiz-questions");
      const questions = await resp.json();
      this.currentQuizQuestions = questions;

      container.innerHTML = "";
      questions.forEach((q, idx) => {
        const qCard = document.createElement("div");
        qCard.className = "bg-slate-900/80 p-3 rounded-xl border border-slate-800 text-xs";
        
        let optionsHtml = "";
        q.options.forEach((opt, optIdx) => {
          optionsHtml += `
            <button onclick="window.SecurityTools.selectQuizAnswer(${idx}, ${optIdx}, this)" class="quiz-opt-btn w-full text-left p-2 rounded-lg bg-slate-950/60 border border-slate-700/60 text-slate-300 hover:border-cyan-500/50 hover:text-white transition mb-1.5 flex items-center gap-2">
              <span class="w-4 h-4 rounded-full border border-slate-500 flex items-center justify-center text-[10px] font-bold">${String.fromCharCode(65 + optIdx)}</span>
              <span>${opt}</span>
            </button>
          `;
        });

        qCard.innerHTML = `
          <div class="font-bold text-slate-200 mb-2">${idx + 1}. ${q.question}</div>
          <div class="space-y-1">${optionsHtml}</div>
        `;
        container.appendChild(qCard);
      });

      const submitBtn = document.createElement("button");
      submitBtn.id = "btnSubmitQuiz";
      submitBtn.className = "cyber-btn mt-2 py-2.5 text-xs";
      submitBtn.innerHTML = "<span>🏆 Natijani hisoblash</span>";
      submitBtn.onclick = () => this.submitQuiz();
      container.appendChild(submitBtn);

    } catch (e) {
      container.innerHTML = `<div class="text-center py-2 text-rose-400">Testni yuklab bo'lmadi.</div>`;
    }
  },

  selectQuizAnswer(questionIdx, optionIdx, btnEl) {
    this.userAnswers[questionIdx] = optionIdx;
    const parent = btnEl.parentElement;
    parent.querySelectorAll(".quiz-opt-btn").forEach(b => {
      b.className = "quiz-opt-btn w-full text-left p-2 rounded-lg bg-slate-950/60 border border-slate-700/60 text-slate-300 mb-1.5 flex items-center gap-2";
    });
    btnEl.className = "quiz-opt-btn w-full text-left p-2 rounded-lg bg-cyan-500/20 border border-cyan-500 text-cyan-300 font-bold mb-1.5 flex items-center gap-2";
  },

  async submitQuiz() {
    const answersArray = [];
    for (let i = 0; i < this.currentQuizQuestions.length; i++) {
      answersArray.push(this.userAnswers[i] !== undefined ? this.userAnswers[i] : -1);
    }

    try {
      const resp = await fetch("/api/tools/quiz-submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answers: answersArray })
      });
      const res = await resp.json();

      const resultBox = document.getElementById("quizResultBox");
      resultBox.classList.remove("hidden");
      resultBox.scrollIntoView({ behavior: "smooth" });

      document.getElementById("quizScoreText").textContent = `${res.correct_count} / ${res.total} (${res.percentage}%)`;
      document.getElementById("quizLevelBadge").textContent = res.level;
      document.getElementById("quizSummaryText").textContent = res.message_uz;

    } catch (e) {
      alert("Natijani hisoblashda xatolik.");
    }
  }
};

document.addEventListener("DOMContentLoaded", () => {
  window.SecurityTools.init();
});
