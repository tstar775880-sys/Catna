const state = {
  plants: [],
  garden: [],
  recommendations: [],
};

const gardenStorageKey = "catna-garden";

const elements = {
  tabs: document.querySelectorAll(".tab-button"),
  panels: document.querySelectorAll(".panel"),
  searchInput: document.querySelector("#plant-search"),
  results: document.querySelector("#results"),
  resultTemplate: document.querySelector("#result-template"),
  recommendationTemplate: document.querySelector("#recommendation-template"),
  indoorList: document.querySelector("#indoor-list"),
  recommendationModal: document.querySelector("#recommendation-modal"),
  modalTitle: document.querySelector("#modal-title"),
  modalSubtitle: document.querySelector("#modal-subtitle"),
  modalContent: document.querySelector("#modal-content"),
  modalClose: document.querySelector("#modal-close"),
  gardenForm: document.querySelector("#garden-form"),
  gardenPlant: document.querySelector("#garden-plant"),
  customName: document.querySelector("#custom-name"),
  wateringDays: document.querySelector("#watering-days"),
  lastWatered: document.querySelector("#last-watered"),
  plantStatus: document.querySelector("#plant-status"),
  gardenList: document.querySelector("#garden-list"),
};

init();

async function init() {
  const [plants, recommendations] = await Promise.all([
    fetchPlants(),
    fetchRecommendations(),
  ]);
  state.plants = plants;
  state.recommendations = recommendations;
  state.garden = loadGarden();
  setDefaultDate();
  bindEvents();
  renderPlantOptions();
  renderResults("");
  renderRecommendations();
  renderGarden();
}

async function fetchPlants() {
  const [curatedResponse, aspcaResponse] = await Promise.all([
    fetch("data/plants.json"),
    fetch("data/aspca_cats_plants.json"),
  ]);
  if (!curatedResponse.ok || !aspcaResponse.ok) {
    throw new Error("無法載入植物資料");
  }

  const curatedPlants = await curatedResponse.json();
  const aspcaData = await aspcaResponse.json();
  return mergePlantData(curatedPlants, aspcaData.plants || []);
}

async function fetchRecommendations() {
  const response = await fetch("data/indoor_recommendations.json");
  if (!response.ok) {
    throw new Error("無法載入室內植物推薦資料");
  }
  return response.json();
}

function mergePlantData(curatedPlants, aspcaPlants) {
  const curatedByScientificName = new Map(
    curatedPlants.map((plant) => [normalizeText(plant.scientificName), plant])
  );
  const curatedByEnglishName = new Map(
    curatedPlants.map((plant) => [normalizeText(plant.commonNameEn), plant])
  );

  const aspcaMapped = aspcaPlants.map((plant) => {
    const curated =
      curatedByScientificName.get(normalizeText(plant.scientific_name)) ||
      curatedByEnglishName.get(normalizeText(plant.common_name_en));

    return {
      id: plant.id,
      commonNameZh: plant.common_name_zh || (curated ? curated.commonNameZh : ""),
      commonNameEn: plant.common_name_en,
      scientificName: plant.scientific_name,
      family: plant.family,
      aliasesZh: [
        ...(plant.aliases_zh || []),
        ...(curated ? curated.aliasesZh || [] : []),
      ],
      aliasesEn: plant.aliases_en || [],
      catToxicity: plant.cat_toxicity,
      catToxicityNote: plant.catToxicityNote || toxicityNoteForAspcaPlant(plant),
      symptoms: plant.symptoms || aspcaSymptomsForPlant(plant, curated),
      care: curated ? curated.care : "尚未整理養護摘要。",
      sourceName: "ASPCA Cats Plant List",
      sourceUrl: plant.source_url,
    };
  });

  const existing = new Set(aspcaMapped.map((plant) => normalizeText(plant.scientificName)));
  const curatedOnly = curatedPlants.filter((plant) => !existing.has(normalizeText(plant.scientificName)));
  return [...aspcaMapped, ...curatedOnly];
}

function toxicityNoteForAspcaPlant(plant) {
  if (plant.cat_toxicity === "caution") {
    return "ASPCA 貓用清單列為需注意；通常是大量食用可能造成腸胃不適，不等同高危險毒物。";
  }
  if (plant.cat_toxicity === "toxic") {
    return "ASPCA 貓用清單列為對貓有毒。";
  }
  return "ASPCA 貓用清單列為對貓無毒。";
}

function aspcaSymptomsForPlant(plant, curated) {
  if (plant.id === "aspca-catnip") {
    return "未列出特定毒性症狀。";
  }
  return curated ? curated.symptoms : "";
}

function bindEvents() {
  elements.tabs.forEach((button) => {
    button.addEventListener("click", () => switchTab(button.dataset.tab));
  });

  elements.searchInput.addEventListener("input", (event) => {
    renderResults(event.target.value);
  });

  elements.gardenForm.addEventListener("submit", (event) => {
    event.preventDefault();
    addGardenPlant();
  });

  elements.modalClose.addEventListener("click", closeRecommendationModal);
  elements.recommendationModal.addEventListener("click", (event) => {
    if (event.target === elements.recommendationModal) {
      closeRecommendationModal();
    }
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !elements.recommendationModal.hidden) {
      closeRecommendationModal();
    }
  });
}

function switchTab(tabId) {
  elements.tabs.forEach((button) => {
    button.classList.toggle("active", button.dataset.tab === tabId);
  });
  elements.panels.forEach((panel) => {
    panel.classList.toggle("active", panel.id === tabId);
  });
}

function normalizeText(value) {
  return String(value || "")
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^\p{L}\p{N}]+/gu, "");
}

function plantSearchFields(plant) {
  return [
    plant.commonNameZh,
    plant.commonNameEn,
    plant.scientificName,
    plant.family,
    ...(plant.aliasesZh || []),
    ...(plant.aliasesEn || []),
  ].filter(Boolean);
}

function scorePlant(plant, rawQuery) {
  const query = normalizeText(rawQuery);
  if (!query) return 1;

  return plantSearchFields(plant).reduce((best, field) => {
    const normalized = normalizeText(field);
    if (!normalized) return best;
    if (normalized === query) return Math.max(best, 120);
    if (normalized.startsWith(query)) return Math.max(best, 95);
    if (normalized.includes(query)) return Math.max(best, 82);

    const maxDistance = query.length <= 4 ? 1 : 2;
    const distance = levenshtein(query, normalized.slice(0, Math.max(query.length + 2, 6)));
    if (distance <= maxDistance) {
      return Math.max(best, 65 - distance * 10);
    }
    return best;
  }, 0);
}

function levenshtein(a, b) {
  const rows = Array.from({ length: a.length + 1 }, () => []);
  for (let i = 0; i <= a.length; i += 1) rows[i][0] = i;
  for (let j = 0; j <= b.length; j += 1) rows[0][j] = j;

  for (let i = 1; i <= a.length; i += 1) {
    for (let j = 1; j <= b.length; j += 1) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      rows[i][j] = Math.min(
        rows[i - 1][j] + 1,
        rows[i][j - 1] + 1,
        rows[i - 1][j - 1] + cost
      );
    }
  }
  return rows[a.length][b.length];
}

function renderResults(query) {
  const matches = state.plants
    .map((plant) => ({ plant, score: scorePlant(plant, query) }))
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score || a.plant.commonNameZh.localeCompare(b.plant.commonNameZh, "zh-Hant"))
    .slice(0, query.trim() ? 12 : 8);

  elements.results.innerHTML = "";
  if (!matches.length) {
    elements.results.innerHTML = '<div class="empty">目前資料庫沒有找到相近植物。請改用學名、英文名或較短關鍵字搜尋。</div>';
    return;
  }

  matches.forEach(({ plant }) => {
    elements.results.appendChild(renderPlantCard(plant));
  });
}

function renderPlantCard(plant) {
  const node = elements.resultTemplate.content.firstElementChild.cloneNode(true);
  node.querySelector("h3").textContent = plant.commonNameZh
    ? `${plant.commonNameZh} / ${plant.commonNameEn}`
    : plant.commonNameEn;
  node.querySelector(".scientific").textContent = plant.scientificName;
  node.querySelector(".aliases").textContent = `別名：${[...(plant.aliasesZh || []), ...(plant.aliasesEn || [])].join("、") || "無"}`;

  const pill = node.querySelector(".status-pill");
  pill.textContent = statusLabel(plant.catToxicity);
  pill.classList.add(statusClass(plant.catToxicity));

  node.querySelector(".toxicity").textContent = plant.catToxicityNote;
  node.querySelector(".symptoms").textContent = plant.symptoms || "資料來源未列出明確症狀。";
  node.querySelector(".care").textContent = plant.care;

  const source = node.querySelector(".source-link");
  source.href = plant.sourceUrl;
  source.textContent = plant.sourceName || "查看來源";
  return node;
}

function renderRecommendations() {
  elements.indoorList.innerHTML = "";

  if (!state.recommendations.length) {
    elements.indoorList.innerHTML = '<div class="empty">尚未整理室內植物推薦。</div>';
    return;
  }

  state.recommendations.forEach((plant) => {
    elements.indoorList.appendChild(renderRecommendationCard(plant));
  });
}

function renderRecommendationCard(plant) {
  const node = elements.recommendationTemplate.content.firstElementChild.cloneNode(true);
  const image = node.querySelector("img");
  const placeholder = node.querySelector(".recommendation-placeholder");
  node.querySelector("strong").textContent = plant.commonNameZh;
  node.querySelector("small").textContent = plant.commonNameEn;

  if (plant.imageUrl) {
    image.src = plant.imageUrl;
    image.alt = plant.imageAlt || plant.commonNameZh;
    image.hidden = false;
    placeholder.hidden = true;
  }

  node.addEventListener("click", () => {
    openRecommendationModal(plant);
  });
  return node;
}

function openRecommendationModal(plant) {
  elements.modalTitle.textContent = `${plant.commonNameZh} / ${plant.commonNameEn}`;
  elements.modalSubtitle.textContent = plant.scientificName;
  elements.modalContent.innerHTML = `
    ${plant.imageUrl ? `
      <figure class="modal-figure">
        <img src="${escapeHtml(plant.imageUrl)}" alt="${escapeHtml(plant.imageAlt || plant.commonNameZh)}">
        <figcaption>${escapeHtml(imageCreditText(plant))}</figcaption>
      </figure>
    ` : ""}
    <p class="modal-safety">${escapeHtml(plant.catSafety)}</p>
    <dl class="recommendation-details">
      <div>
        <dt>擺放類型</dt>
        <dd>${escapeHtml(plant.placementType)}</dd>
      </div>
      <div>
        <dt>成熟尺寸</dt>
        <dd>${escapeHtml(plant.matureSize)}</dd>
      </div>
      <div>
        <dt>難度</dt>
        <dd>${escapeHtml(plant.difficulty)}</dd>
      </div>
      <div>
        <dt>光照</dt>
        <dd>${escapeHtml(plant.light)}</dd>
      </div>
      <div>
        <dt>澆水頻率</dt>
        <dd>${escapeHtml(plant.wateringFrequency)}</dd>
      </div>
      <div>
        <dt>澆水方式</dt>
        <dd>${escapeHtml(plant.wateringMethod)}</dd>
      </div>
      <div>
        <dt>濕度</dt>
        <dd>${escapeHtml(plant.humidity)}</dd>
      </div>
      <div>
        <dt>溫度</dt>
        <dd>${escapeHtml(plant.temperature)}</dd>
      </div>
      <div>
        <dt>推薦理由</dt>
        <dd>${escapeHtml(plant.whyRecommended)}</dd>
      </div>
    </dl>
    <p class="watchouts">注意：${escapeHtml(plant.watchouts)}</p>
    <p class="source-line">來源：${plant.sourceUrls
      .map((url, index) => `<a href="${escapeHtml(url)}" target="_blank" rel="noreferrer">${escapeHtml(plant.sourceNames[index] || "來源")}</a>`)
      .join("、")}</p>
  `;
  elements.recommendationModal.hidden = false;
  document.body.classList.add("modal-open");
  elements.modalClose.focus();
}

function imageCreditText(plant) {
  const parts = [plant.imageCredit, plant.imageLicense].filter(Boolean);
  return parts.length ? parts.join(" / ") : "圖片來源待補";
}

function closeRecommendationModal() {
  elements.recommendationModal.hidden = true;
  document.body.classList.remove("modal-open");
}

function statusLabel(status) {
  const labels = {
    toxic: "對貓有毒",
    caution: "需注意用量",
    safe: "對貓低風險或列為無毒",
    unknown: "資料不足",
  };
  return labels[status] || labels.unknown;
}

function statusClass(status) {
  return {
    toxic: "status-toxic",
    caution: "status-caution",
    safe: "status-safe",
    unknown: "status-unknown",
  }[status] || "status-unknown";
}

function renderPlantOptions() {
  elements.gardenPlant.innerHTML = state.plants
    .map((plant) => `<option value="${plant.id}">${plant.commonNameZh} / ${plant.commonNameEn}</option>`)
    .join("");
}

function setDefaultDate() {
  elements.lastWatered.value = new Date().toISOString().slice(0, 10);
}

function addGardenPlant() {
  const plant = state.plants.find((item) => item.id === elements.gardenPlant.value);
  if (!plant) return;

  state.garden.push({
    id: crypto.randomUUID(),
    plantId: plant.id,
    name: elements.customName.value.trim() || plant.commonNameZh,
    wateringDays: Number(elements.wateringDays.value || 7),
    lastWatered: elements.lastWatered.value,
    status: elements.plantStatus.value,
    createdAt: new Date().toISOString(),
  });

  saveGarden();
  elements.customName.value = "";
  renderGarden();
}

function renderGarden() {
  elements.gardenList.innerHTML = "";

  if (!state.garden.length) {
    elements.gardenList.innerHTML = '<div class="empty">尚未追蹤植物。</div>';
    return;
  }

  state.garden.forEach((item) => {
    const plant = state.plants.find((candidate) => candidate.id === item.plantId);
    const due = nextWateringDate(item.lastWatered, item.wateringDays);
    const article = document.createElement("article");
    article.className = "garden-item";
    article.innerHTML = `
      <div class="garden-item-head">
        <div>
          <h3>${escapeHtml(item.name)}</h3>
          <p class="garden-meta">${escapeHtml(plant ? plant.commonNameZh : "未知植物")} / ${escapeHtml(plant ? plant.scientificName : "")}</p>
        </div>
        <button class="remove-button" type="button" data-id="${item.id}">移除</button>
      </div>
      <dl class="plant-details">
        <div>
          <dt>對貓狀態</dt>
          <dd>${plant ? statusLabel(plant.catToxicity) : "資料不足"}</dd>
        </div>
        <div>
          <dt>下次澆水</dt>
          <dd>${due}</dd>
        </div>
        <div>
          <dt>目前狀況</dt>
          <dd>${escapeHtml(item.status)}</dd>
        </div>
      </dl>
      <p class="garden-meta">${escapeHtml(plant ? plant.care : "")}</p>
    `;
    article.querySelector(".remove-button").addEventListener("click", () => {
      state.garden = state.garden.filter((candidate) => candidate.id !== item.id);
      saveGarden();
      renderGarden();
    });
    elements.gardenList.appendChild(article);
  });
}

function nextWateringDate(lastWatered, days) {
  if (!lastWatered) return "未設定";
  const date = new Date(`${lastWatered}T00:00:00`);
  date.setDate(date.getDate() + Number(days || 7));
  return date.toISOString().slice(0, 10);
}

function loadGarden() {
  try {
    return JSON.parse(localStorage.getItem(gardenStorageKey)) || [];
  } catch {
    return [];
  }
}

function saveGarden() {
  localStorage.setItem(gardenStorageKey, JSON.stringify(state.garden));
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
