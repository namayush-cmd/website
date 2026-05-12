async function loadDashboardAnalytics() {

    let ctx1 = document.getElementById("dashboardChartMain");
    let ctx2 = document.getElementById("dashboardChartStatus");

    if (!ctx1 || !ctx2) {
        console.log("❌ Canvas not ready");
        return;
    }

    try {
        // 🔹 1. FETCH UTILIZATION DATA
        let res = await fetch("/report_data");

        if (!res.ok) {
            console.error("❌ report_data API failed");
            return;
        }

        let data = await res.json();

        let labels = [];
        let totals = [];

        // 🔥 ALL YEARS COMBINED
        for (let state in data) {
            labels.push(state);

            let sum = 0;

            for (let year in data[state]) {
                let d = data[state][year];

                sum += (d["Ayush Services"] || 0) +
                       (d["Educational Institutions"] || 0) +
                       (d["Medicinal Plants"] || 0) +
                       (d["Quality Control"] || 0) +
                       (d["Flexi Pool"] || 0) +
                       (d["Admin Cost"] || 0);
            }

            totals.push(sum);
        }

        // 🔹 Destroy old charts
        if (window.barChart) window.barChart.destroy();
        if (window.donutChart) window.donutChart.destroy();

        // 🔵 BAR CHART
        window.barChart = new Chart(ctx1, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [{
                    label: "Total Utilization (Rs. in Lakhs)",
                    data: totals,
                    backgroundColor: "#2196f3"
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "top"
                    },
                    title: {
                        display: true,
                        text: "State-wise Total Utilization (All Years)"
                    }
                },
                scales: {
                    y: {
                        title: {
                            display: true,
                            text: "Amount (Rs. in Lakhs)"
                        }
                    }
                }
            }
        });

        // 🔹 2. FETCH STATUS DATA
        let resStatus = await fetch("/report_data");

        if (!resStatus.ok) {
            console.error("❌ report_data API failed");
            return;
        }

        let statusData = await resStatus.json();

        let TOTAL_STATES = 36;
        let submitted = 0;

        // 🔥 CHECK ANY YEAR SUBMITTED
        for (let state in statusData) {

            let hasSubmitted = false;

            for (let year in statusData[state]) {
                if (statusData[state][year]) {
                    hasSubmitted = true;
                    break;
                }
            }

            if (hasSubmitted) {
                submitted++;
            }
        }

        let awaited = TOTAL_STATES - submitted;

        console.log("✅ Submitted:", submitted);
        console.log("⏳ Awaited:", awaited);

        // 🟢🔴 PIE / DONUT CHART
        window.donutChart = new Chart(ctx2, {
            type: "doughnut",
            data: {
                labels: [
                    `Submitted (${submitted})`,
                    `Awaited (${awaited})`
                ],
                datasets: [{
                    data: [submitted, awaited],
                    backgroundColor: [
                        "#4CAF50",
                        "#F44336"
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "60%",
                plugins: {
                    legend: {
                        position: "top"
                    },
                    title: {
                        display: true,
                        text: "Submission Status (All Years)"
                    }
                }
            }
        });

    } catch (err) {
        console.error("❌ Dashboard Error:", err);
    }
}