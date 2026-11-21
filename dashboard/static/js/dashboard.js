const chartSource = JSON.parse(document.getElementById("lobbies_count_per_day").textContent);
const dayMs = 24 * 60 * 60 * 1000;
const rawDailyPoints = chartSource.labels.map((label, index) => ({
    date: label,
    x: Date.parse(`${label}T00:00:00Z`),
    y: chartSource.data[index],
}));

function isoDate(timestamp) {
    return new Date(timestamp).toISOString().slice(0, 10);
}

function bucketBounds(timestamp, granularity) {
    const date = new Date(timestamp);
    let start;
    let end;

    if (granularity === "month") {
        start = Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), 1);
        end = Date.UTC(date.getUTCFullYear(), date.getUTCMonth() + 1, 0);
    } else if (granularity === "week") {
        const mondayOffset = (date.getUTCDay() + 6) % 7;
        start = Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate() - mondayOffset);
        end = start + (6 * dayMs);
    } else {
        start = timestamp;
        end = timestamp;
    }
    return { start, end };
}

function aggregatePoints(granularity) {
    const buckets = new Map();
    rawDailyPoints.forEach((point) => {
        const bounds = bucketBounds(point.x, granularity);
        const key = bounds.start;
        if (!buckets.has(key)) {
            buckets.set(key, { x: key, y: 0, bucketStart: isoDate(bounds.start), bucketEnd: isoDate(bounds.end) });
        }
        buckets.get(key).y += point.y;
    });
    return Array.from(buckets.values());
}

function granularityForSpan(spanMs) {
    const days = spanMs / dayMs;
    if (days > 730) return "month";
    if (days > 120) return "week";
    return "day";
}

function granularityLabel(granularity) {
    return { day: "Daily values", week: "Weekly totals", month: "Monthly totals" }[granularity];
}

const sourceSpan = rawDailyPoints.length > 1
    ? rawDailyPoints[rawDailyPoints.length - 1].x - rawDailyPoints[0].x
    : 0;
let currentGranularity = granularityForSpan(sourceSpan);
const initialChartPoints = aggregatePoints(currentGranularity);
document.getElementById("chartGranularity").textContent = `${granularityLabel(currentGranularity)} · scroll to zoom, drag to move.`;

const ctx = document.getElementById("lineChart").getContext("2d");
const lineChart = new Chart(ctx, {
    type: "line",
    data: {
        datasets: [{
            label: "Lobbies",
            data: initialChartPoints,
            parsing: false,
            borderColor: "#087f5b",
            backgroundColor: "rgba(8, 127, 91, .12)",
            borderWidth: 2,
            fill: true,
            tension: .28,
            pointRadius: initialChartPoints.length > 100 ? 0 : 2,
            pointHoverRadius: 6,
            pointBackgroundColor: "#087f5b",
        }],
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { intersect: false, mode: "nearest" },
        scales: {
            x: {
                type: "time",
                time: { unit: currentGranularity },
                grid: { display: false },
                ticks: { color: "#65727a", maxRotation: 0, autoSkipPadding: 26 },
            },
            y: {
                beginAtZero: true,
                grace: "8%",
                grid: { color: "rgba(101, 114, 122, .13)" },
                ticks: { color: "#65727a", precision: 0 },
            },
        },
        plugins: {
            legend: { display: false },
            tooltip: {
                displayColors: false,
                callbacks: {
                    title(items) {
                        if (!items.length) return "";
                        const point = items[0].raw;
                        return point.bucketStart === point.bucketEnd
                            ? point.bucketStart
                            : `${point.bucketStart} – ${point.bucketEnd}`;
                    },
                    label(item) { return `${item.raw.y} ${item.raw.y === 1 ? "lobby" : "lobbies"}`; },
                },
            },
            zoom: {
                limits: { x: { min: "original", max: "original", minRange: 2 * dayMs } },
                pan: { enabled: true, mode: "x", threshold: 4, onPanComplete: refreshChartAggregation },
                zoom: {
                    wheel: { enabled: true, speed: .08 },
                    pinch: { enabled: true },
                    mode: "x",
                    onZoomComplete: refreshChartAggregation,
                },
            },
        },
        onClick(event, elements) {
            if (!elements.length) return;
            const point = lineChart.data.datasets[elements[0].datasetIndex].data[elements[0].index];
            tableState.dateFrom = point.bucketStart;
            tableState.dateTo = point.bucketEnd;
            document.getElementById("tableContext").textContent = `Showing lobbies from ${point.bucketStart} to ${point.bucketEnd}.`;
            document.getElementById("tableScroll").scrollTop = 0;
            loadLobbies(true);
        },
    },
});

function refreshChartAggregation({ chart } = { chart: lineChart }) {
    const scale = chart.scales.x;
    const granularity = granularityForSpan(scale.max - scale.min);
    if (granularity === currentGranularity) return;
    currentGranularity = granularity;
    const points = aggregatePoints(granularity);
    chart.data.datasets[0].data = points;
    chart.data.datasets[0].pointRadius = points.length > 100 ? 0 : 2;
    chart.options.scales.x.time.unit = granularity;
    document.getElementById("chartGranularity").textContent = `${granularityLabel(granularity)} · grouped automatically for this view.`;
    chart.update("none");
}

document.getElementById("resetZoomBtn").addEventListener("click", () => {
    lineChart.resetZoom();
    refreshChartAggregation();
});

const query = new URLSearchParams(window.location.search);
const tableState = {
    page: 1,
    pageSize: 30,
    sort: "created_at",
    direction: "desc",
    status: "all",
    dateFrom: query.get("date_from") || "",
    dateTo: query.get("date_to") || "",
    loading: false,
    hasMore: true,
    loaded: 0,
    total: 0,
    requestNumber: 0,
};

const tableBody = document.getElementById("lobbyTableBody");
const loadingState = document.getElementById("loadingState");
const emptyState = document.getElementById("emptyState");
const loadMoreBtn = document.getElementById("loadMoreBtn");

function lobbyApiUrl() {
    const url = new URL("/dashboard/lobbies/", window.location.origin);
    url.searchParams.set("page", tableState.page);
    url.searchParams.set("page_size", tableState.pageSize);
    url.searchParams.set("sort", tableState.sort);
    url.searchParams.set("direction", tableState.direction);
    if (tableState.status !== "all") url.searchParams.set("status", tableState.status);
    if (tableState.dateFrom) url.searchParams.set("date_from", tableState.dateFrom);
    if (tableState.dateTo) url.searchParams.set("date_to", tableState.dateTo);
    return url;
}

function formatCreatedAt(value) {
    return new Intl.DateTimeFormat("en-GB", {
        dateStyle: "medium",
        timeStyle: "short",
        timeZone: "Europe/Berlin",
    }).format(new Date(value));
}

function makeCell(content, className = "") {
    const cell = document.createElement("td");
    cell.className = className;
    if (content instanceof Node) cell.appendChild(content);
    else cell.textContent = content;
    return cell;
}

function appendLobbyRow(lobby) {
    const row = document.createElement("tr");
    row.id = `row-${lobby.lobby_id}`;

    const idButton = document.createElement("button");
    idButton.type = "button";
    idButton.className = "id-button";
    idButton.textContent = lobby.lobby_id;
    idButton.title = lobby.lobby_id;
    idButton.addEventListener("click", () => getLobbyJson(lobby.lobby_id, lobby.game));

    const status = document.createElement("span");
    status.className = `status-pill${lobby.game ? "" : " empty"}`;
    status.textContent = lobby.game ? "Started" : "Empty";

    row.appendChild(makeCell(idButton));
    row.appendChild(makeCell(formatCreatedAt(lobby.time_created)));
    row.appendChild(makeCell(lobby.amount_players ?? "—"));
    row.appendChild(makeCell(lobby.amount_ai_players ?? "—"));
    row.appendChild(makeCell(status));

    const link = document.createElement("a");
    link.className = "open-link";
    link.textContent = lobby.game ? "Open" : "";
    if (lobby.game) {
        link.href = `/game/${lobby.lobby_id}`;
        link.target = "_blank";
        link.rel = "noopener";
    }
    row.appendChild(makeCell(link));
    tableBody.appendChild(row);
}

async function loadLobbies(reset = false) {
    if (tableState.loading && !reset) return;
    if (!tableState.hasMore && !reset) return;

    if (reset) {
        tableState.page = 1;
        tableState.hasMore = true;
        tableState.loaded = 0;
        tableBody.replaceChildren();
    }

    tableState.loading = true;
    const requestNumber = ++tableState.requestNumber;
    loadingState.hidden = false;
    emptyState.hidden = true;
    loadMoreBtn.disabled = true;

    try {
        const response = await fetch(lobbyApiUrl(), { headers: { Accept: "application/json" } });
        if (!response.ok) throw new Error(`Request failed (${response.status})`);
        const payload = await response.json();
        if (requestNumber !== tableState.requestNumber) return;

        payload.results.forEach(appendLobbyRow);
        tableState.loaded += payload.results.length;
        tableState.total = payload.total;
        tableState.hasMore = payload.has_more;
        if (payload.has_more) tableState.page += 1;

        document.getElementById("tableCount").textContent = payload.total.toLocaleString();
        document.getElementById("loadedCount").textContent = `${tableState.loaded.toLocaleString()} of ${payload.total.toLocaleString()} loaded`;
        emptyState.hidden = payload.total !== 0;
        loadMoreBtn.hidden = !payload.has_more;
    } catch (error) {
        showToast(error.message || "Could not load lobbies.", true);
    } finally {
        if (requestNumber === tableState.requestNumber) {
            tableState.loading = false;
            loadingState.hidden = true;
            loadMoreBtn.disabled = false;
        }
    }
}

document.querySelectorAll(".sort-button").forEach((button) => {
    button.addEventListener("click", () => {
        const sort = button.dataset.sort;
        tableState.direction = tableState.sort === sort && tableState.direction === "desc" ? "asc" : "desc";
        tableState.sort = sort;
        document.querySelectorAll(".sort-button").forEach((item) => item.classList.remove("active", "asc", "desc"));
        button.classList.add("active", tableState.direction);
        loadLobbies(true);
    });
});

document.getElementById("statusSelect").addEventListener("change", (event) => {
    tableState.status = event.target.value;
    loadLobbies(true);
});
document.getElementById("pageSizeSelect").addEventListener("change", (event) => {
    tableState.pageSize = Number(event.target.value);
    loadLobbies(true);
});
loadMoreBtn.addEventListener("click", () => loadLobbies());

const observer = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) loadLobbies();
}, { root: document.getElementById("tableScroll"), rootMargin: "180px" });
observer.observe(document.getElementById("loadSentinel"));

function setDateRange(daysBack) {
    const url = new URL(window.location.href);
    url.searchParams.delete("date_to");
    if (daysBack === "all") {
        url.searchParams.delete("date_from");
    } else {
        const date = new Date();
        date.setHours(12, 0, 0, 0);
        date.setDate(date.getDate() - Number(daysBack));
        url.searchParams.set("date_from", `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`);
    }
    window.location.assign(url);
}

document.querySelectorAll("[data-range]").forEach((button) => {
    button.addEventListener("click", () => setDateRange(button.dataset.range));
});

const activeRange = (() => {
    const from = query.get("date_from");
    if (!from) return "all";
    const today = new Date();
    today.setHours(12, 0, 0, 0);
    const fromDate = new Date(`${from}T12:00:00`);
    return String(Math.round((today - fromDate) / dayMs));
})();
document.querySelector(`[data-range="${activeRange}"]`)?.classList.add("active");

async function getLobbyJson(lobbyId, hasGame) {
    document.querySelectorAll("#lobbyTableBody tr").forEach((row) => row.classList.toggle("selected", row.id === `row-${lobbyId}`));
    const container = document.getElementById("selectedGameJsonContainer");
    container.innerHTML = '<div class="loading-state"><span class="spinner"></span>Loading lobby…</div>';
    try {
        const response = await fetch(`/get_game_data/${lobbyId}`, { headers: { Accept: "application/json" } });
        if (!response.ok) throw new Error(`Request failed (${response.status})`);
        const payload = await response.json();
        container.replaceChildren();
        const viewer = new JSONViewer();
        container.appendChild(viewer.getContainer());
        viewer.showJSON(payload.lobby, -1, 2);
        document.getElementById("selectedLobbyHint").textContent = lobbyId;
        const link = document.getElementById("selectedLobbyLink");
        link.hidden = !hasGame;
        link.href = hasGame ? `/game/${lobbyId}` : "#";
    } catch (error) {
        container.innerHTML = '<div class="empty-state">The lobby data could not be loaded.</div>';
        showToast(error.message, true);
    }
}

let toastTimer;
function showToast(message, isError = false) {
    const toast = document.getElementById("toast");
    toast.textContent = message;
    toast.classList.toggle("error", isError);
    toast.classList.add("visible");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove("visible"), 3200);
}

document.getElementById("deleteEmptyBtn").addEventListener("click", async () => {
    if (!window.confirm("Delete all lobbies without game data? This cannot be undone.")) return;
    const button = document.getElementById("deleteEmptyBtn");
    button.disabled = true;
    try {
        const response = await fetch("/dashboard/delete_empty_lobbies/", {
            method: "DELETE",
            headers: { "X-CSRFToken": getCookie("csrftoken", ""), Accept: "application/json" },
        });
        if (!response.ok) throw new Error(`Delete failed (${response.status})`);
        const payload = await response.json();
        showToast(`${payload.deleted} empty lobbies deleted.`);
        window.setTimeout(() => window.location.reload(), 700);
    } catch (error) {
        showToast(error.message, true);
        button.disabled = false;
    }
});

loadLobbies(true);
