let activeCharts = [];

export function destroyCharts() {
  activeCharts.forEach(chart => chart.destroy());
  activeCharts = [];
}

export function createLineChart(canvasId, labels, values, label = "Trend") {
  const ctx = document.getElementById(canvasId);

  const chart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label,
          data: values,
          borderColor: "#818CF8",
          backgroundColor: "rgba(129, 140, 248, 0.18)",
          fill: true,
          tension: 0.42,
          borderWidth: 3,
          pointRadius: 4
        }
      ]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: "#64748B" }
        },
        y: {
          grid: { color: "rgba(148,163,184,0.2)" },
          ticks: { color: "#64748B" }
        }
      }
    }
  });

  activeCharts.push(chart);
}

export function createBarChart(canvasId, labels, values, label = "Values") {
  const ctx = document.getElementById(canvasId);

  const chart = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label,
          data: values,
          backgroundColor: "#4F46E5",
          borderRadius: 10
        }
      ]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: "#64748B" }
        },
        y: {
          grid: { color: "rgba(148,163,184,0.2)" },
          ticks: { color: "#64748B" }
        }
      }
    }
  });

  activeCharts.push(chart);
}

export function createDoughnutChart(canvasId, labels, values, colors) {
  const ctx = document.getElementById(canvasId);

  const chart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels,
      datasets: [
        {
          data: values,
          backgroundColor: colors,
          borderWidth: 0,
          cutout: "70%"
        }
      ]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false }
      }
    }
  });

  activeCharts.push(chart);
}