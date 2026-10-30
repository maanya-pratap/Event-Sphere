// Wraps Chart.js with EventSphere's palette so every dashboard chart looks consistent.
// Usage: renderBarChart('canvasId', ['A','B'], [3,7], 'Registrations')

const CHART_COLORS = {
  violet: "#7c5cff",
  mint: "#00e5a0",
  coral: "#ff5d73",
  gold: "#ffc857",
  grid: "rgba(167,159,209,0.15)",
  text: "#a79fd1",
};

function baseOptions() {
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { labels: { color: CHART_COLORS.text } } },
    scales: {
      x: { ticks: { color: CHART_COLORS.text }, grid: { color: CHART_COLORS.grid } },
      y: { ticks: { color: CHART_COLORS.text }, grid: { color: CHART_COLORS.grid }, beginAtZero: true },
    },
  };
}

function renderBarChart(canvasId, labels, data, label) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [{ label, data, backgroundColor: CHART_COLORS.violet, borderRadius: 8, maxBarThickness: 42 }],
    },
    options: baseOptions(),
  });
}

function renderDoughnut(canvasId, labels, data) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  new Chart(ctx, {
    type: "doughnut",
    data: {
      labels,
      datasets: [{ data, backgroundColor: [CHART_COLORS.mint, CHART_COLORS.coral, CHART_COLORS.gold] }],
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: CHART_COLORS.text } } } },
  });
}
