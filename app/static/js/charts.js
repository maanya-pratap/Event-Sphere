// Wraps Chart.js with EventSphere's palette so every dashboard chart looks consistent.
// Usage: renderBarChart('canvasId', ['A','B'], [3,7], 'Registrations')

const CHART_COLORS = {
  lilac: "#A8A3EC",
  ink: "#2B2620",
  sage: "#A8B97A",
  pink: "#F6B8D9",
  yellow: "#F8DA6B",
  coral: "#F28C8C",
  grid: "rgba(20,17,15,0.08)",
  text: "#5A5143",
};

function baseOptions() {
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { labels: { color: CHART_COLORS.text } } },
    scales: {
      x: {
        ticks: { color: CHART_COLORS.text },
        grid: { color: CHART_COLORS.grid },
      },
      y: {
        ticks: { color: CHART_COLORS.text },
        grid: { color: CHART_COLORS.grid },
        beginAtZero: true,
      },
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
      datasets: [
        {
          label,
          data,
          backgroundColor: CHART_COLORS.lilac,
          borderRadius: 8,
          maxBarThickness: 42,
        },
      ],
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
      datasets: [
        {
          data,
          backgroundColor: [
            CHART_COLORS.sage,
            CHART_COLORS.coral,
            CHART_COLORS.yellow,
          ],
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { labels: { color: CHART_COLORS.text } } },
    },
  });
}
