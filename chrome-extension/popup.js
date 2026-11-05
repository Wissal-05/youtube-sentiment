// ========================================
// CONFIGURATION
// ========================================

// URL publique du Codespace (port 7860). Le "/" final est retiré automatiquement.
const API_URL = "https://shiny-sniffle-69w7r47j4645cgg6-7860.app.github.dev/".replace(/\/+$/, "");

const MAX_COMMENTS = 200;

let results = [];

const $ = id => document.getElementById(id);

// Correspondance label numérique -> clé API
const LABEL_TO_KEY = { "1": "positive", "0": "neutral", "-1": "negative" };

// Affichage (libellé français + classe CSS)
const DISPLAY = {
  positive: { label: "Positif", css: "positif" },
  neutral: { label: "Neutre", css: "neutre" },
  negative: { label: "Négatif", css: "négatif" }
};

// Retourne "positive" | "neutral" | "negative" quel que soit le format renvoyé par l'API
function sentimentKey(r) {
  if (typeof r.sentiment === "string") {
    const s = r.sentiment.toLowerCase();
    if (["positive", "positif"].includes(s)) return "positive";
    if (["neutral", "neutre"].includes(s)) return "neutral";
    if (["negative", "négatif", "negatif"].includes(s)) return "negative";
  }
  return LABEL_TO_KEY[String(r.label)] || null;
}

// Protection contre l'injection HTML
function escapeHtml(s) {
  return String(s ?? "").replace(/[&<>"']/g, c => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  }[c]));
}

// ========================================
// 1. ANALYSE DES COMMENTAIRES
// ========================================

$("analyze").addEventListener("click", async () => {
  $("status").textContent = "Extraction des commentaires...";
  $("analyze").disabled = true;

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    if (!tab || !tab.url?.startsWith("https://www.youtube.com/")) {
      throw new Error("Veuillez ouvrir une page YouTube.");
    }

    // Extraction depuis content.js
    let response;
    try {
      response = await chrome.tabs.sendMessage(tab.id, {
        action: "extract",
        max: MAX_COMMENTS
      });
    } catch (error) {
      throw new Error("Impossible de communiquer avec YouTube. Actualisez la page (F5).");
    }

    const comments = response?.comments || [];

    if (comments.length === 0) {
      throw new Error("Aucun commentaire trouvé. Faites défiler la page jusqu'aux commentaires.");
    }

    $("status").textContent = `Analyse de ${comments.length} commentaires...`;

    // Appel à l'API
    let res;
    try {
      res = await fetch(`${API_URL}/predict_batch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ comments })
      });
    } catch (error) {
      throw new Error("API injoignable. Vérifiez que le Codespace est allumé et le port 7860 public.");
    }

    if (!res.ok) {
      throw new Error(`Erreur API : ${res.status}`);
    }

    const data = await res.json();

    if (!Array.isArray(data.predictions)) {
      throw new Error("Format de réponse API invalide.");
    }

    results = data.predictions;

    renderStats(data.statistics);

    // Réinitialiser le filtre sur "Tous"
    document.querySelectorAll("#filters button").forEach(b => {
      b.classList.toggle("active", b.dataset.f === "all");
    });
    renderList("all");

    $("status").textContent =
      `Terminé : ${results.length} commentaires analysés en ${data.processing_time_ms} ms.`;

  } catch (error) {
    $("status").textContent = "Erreur : " + error.message;
  } finally {
    $("analyze").disabled = false;
  }
});

// ========================================
// 2. AFFICHAGE DES STATISTIQUES
// ========================================

function renderStats(s) {
  if (!s || !s.percentages || !s.counts) {
    $("stats").textContent = "Statistiques indisponibles.";
    return;
  }

  $("stats").innerHTML = Object.keys(DISPLAY).map(key => {
    const item = DISPLAY[key];
    const percentage = Number(s.percentages[key] ?? 0);
    const count = Number(s.counts[key] ?? 0);

    return `
      <div class="bar-row">
        ${item.label} : ${percentage}% (${count})
        <div class="bar">
          <div class="fill ${item.css}"
               style="width: ${Math.max(0, Math.min(100, percentage))}%"></div>
        </div>
      </div>
    `;
  }).join("");
}

// ========================================
// 3. AFFICHAGE DES COMMENTAIRES
// ========================================

function renderList(filter) {
  const items = results.filter(r => filter === "all" || sentimentKey(r) === filter);

  if (items.length === 0) {
    $("list").innerHTML = "<li>Aucun commentaire dans cette catégorie.</li>";
    return;
  }

  $("list").innerHTML = items.map(r => {
    const key = sentimentKey(r);
    const label = key ? DISPLAY[key].label : "Inconnu";
    const confidence = Math.round(Number(r.confidence || 0) * 100);

    return `
      <li class="s${escapeHtml(r.label)}">
        ${escapeHtml((r.text || "").slice(0, 150))}
        <small>${escapeHtml(label)} (${confidence}%)</small>
      </li>
    `;
  }).join("");
}

// ========================================
// 4. FILTRES DE SENTIMENTS
// ========================================

document.querySelectorAll("#filters button").forEach(button => {
  button.addEventListener("click", () => {
    document.querySelectorAll("#filters button")
      .forEach(b => b.classList.remove("active"));

    button.classList.add("active");
    renderList(button.dataset.f);
  });
});

// ========================================
// 5. MODE SOMBRE / MODE CLAIR
// ========================================

$("theme").addEventListener("click", () => {
  document.body.classList.toggle("dark");
  const dark = document.body.classList.contains("dark");
  chrome.storage.local.set({ dark });
  $("theme").textContent = dark ? "☀️" : "🌙";
});

// Restaurer le thème enregistré
chrome.storage.local.get("dark", ({ dark }) => {
  if (dark) {
    document.body.classList.add("dark");
    $("theme").textContent = "☀️";
  }
});

// ========================================
// 6. COPIER LES RÉSULTATS
// ========================================

$("copy").addEventListener("click", async () => {
  if (results.length === 0) {
    $("status").textContent = "Aucun résultat à copier.";
    return;
  }

  const txt = results.map(r => {
    const key = sentimentKey(r);
    const label = key ? DISPLAY[key].label : "Inconnu";
    const confidence = Math.round(Number(r.confidence || 0) * 100);
    return `[${label} - ${confidence}%] ${r.text}`;
  }).join("\n");

  try {
    await navigator.clipboard.writeText(txt);
    $("status").textContent = "Résultats copiés dans le presse-papiers !";
  } catch (error) {
    $("status").textContent = "Impossible de copier les résultats.";
  }
});