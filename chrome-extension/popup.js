
const API_URL = "http://localhost:8000";

let results = [];

const $ = id => document.getElementById(id);

// Correspondance des sentiments
const SENTIMENTS = {
  1: { label: "Positif", css: "positif" },
  0: { label: "Neutre", css: "neutre" },
  "-1": { label: "Négatif", css: "négatif" }
};

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
    // Récupérer l'onglet actif
    const [tab] = await chrome.tabs.query({
      active: true,
      currentWindow: true
    });

    if (!tab || !tab.url?.startsWith("https://www.youtube.com/")) {
      throw new Error("Veuillez ouvrir une page YouTube.");
    }

    // Extraire les commentaires depuis content.js
    let response;

    try {
      response = await chrome.tabs.sendMessage(tab.id, {
        action: "extract"
      });
    } catch (error) {
      throw new Error(
        "Impossible de communiquer avec YouTube. Actualisez la page."
      );
    }

    const comments = response?.comments || [];

    if (comments.length === 0) {
      throw new Error(
        "Aucun commentaire trouvé. Faites défiler la page jusqu'aux commentaires."
      );
    }

    $("status").textContent =
      `Analyse de ${comments.length} commentaires...`;

    // Envoyer les commentaires à FastAPI
    const res = await fetch(`${API_URL}/predict_batch`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ comments })
    });

    if (!res.ok) {
      throw new Error(`Erreur API : ${res.status}`);
    }

    const data = await res.json();

    // Récupérer les prédictions
    if (!Array.isArray(data.predictions)) {
      throw new Error("Format de réponse API invalide.");
    }

    results = data.predictions;

    // Afficher les statistiques
    renderStats(data.statistics);

    // Afficher tous les commentaires
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

  const sentiments = [
    { key: "positive", label: "Positif", css: "positif" },
    { key: "neutral", label: "Neutre", css: "neutre" },
    { key: "negative", label: "Négatif", css: "négatif" }
  ];

  $("stats").innerHTML = sentiments.map(item => {

    const percentage = Number(s.percentages[item.key] ?? 0);
    const count = Number(s.counts[item.key] ?? 0);

    return `
      <div class="bar-row">
        ${item.label} : ${percentage}% (${count})

        <div class="bar">
          <div
            class="fill ${item.css}"
            style="width: ${Math.max(0, Math.min(100, percentage))}%">
          </div>
        </div>
      </div>
    `;

  }).join("");
}

// ========================================
// 3. AFFICHAGE DES COMMENTAIRES
// ========================================

function renderList(filter) {

  const items = results.filter(r =>
    filter === "all" || String(r.label) === filter
  );

  $("list").innerHTML = items.map(r => {

    const sentiment = SENTIMENTS[r.label];

    const label = sentiment
      ? sentiment.label
      : (r.sentiment || "Inconnu");

    const cssClass = sentiment
      ? sentiment.css
      : "";

    const confidence = Math.round(
      Number(r.confidence || 0) * 100
    );

    return `
      <li class="s${r.label}">
        ${escapeHtml((r.text || "").slice(0, 150))}

        <small>
          ${escapeHtml(label)} (${confidence}%)
        </small>
      </li>
    `;

  }).join("");

  if (items.length === 0) {
    $("list").innerHTML =
      "<li>Aucun commentaire dans cette catégorie.</li>";
  }
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
    $("status").textContent =
      "Aucun résultat à copier.";

    return;
  }

  const txt = results.map(r => {

    const sentiment = SENTIMENTS[r.label];

    const label = sentiment
      ? sentiment.label
      : (r.sentiment || "Inconnu");

    const confidence = Math.round(
      Number(r.confidence || 0) * 100
    );

    return `[${label} - ${confidence}%] ${r.text}`;

  }).join("\n");

  try {

    await navigator.clipboard.writeText(txt);

    $("status").textContent =
      "Résultats copiés dans le presse-papiers !";

  } catch (error) {

    $("status").textContent =
      "Impossible de copier les résultats.";

  }

});
