document.addEventListener('DOMContentLoaded', () => {
    const gapAnalysisChartEl = document.getElementById('gapAnalysisChart');
    if (!gapAnalysisChartEl) return;

    fetch('/gap-data')
        .then(response => response.json())
        .then(data => {
            // Bar Chart
            new Chart(gapAnalysisChartEl, {
                type: 'bar',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Skill Proficiency (%)',
                        data: data.percentages,
                        backgroundColor: data.percentages.map(p => p > 50 ? 'rgba(59, 130, 246, 0.8)' : 'rgba(239, 68, 68, 0.8)'),
                        borderColor: 'rgba(255,255,255,0.1)',
                        borderWidth: 1,
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { labels: { color: '#f8fafc' } }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            ticks: { color: '#94a3b8' },
                            grid: { color: 'rgba(255,255,255,0.1)' }
                        },
                        x: {
                            ticks: { color: '#94a3b8' },
                            grid: { display: false }
                        }
                    }
                }
            });

            // Update Overall Missing HTML
            document.getElementById('overall-missing').textContent = `${data.missing_percentage}% of required skills are missing`;

            // Pie Chart
            const gapPieChartEl = document.getElementById('gapPieChart');
            new Chart(gapPieChartEl, {
                type: 'doughnut',
                data: {
                    labels: ['Proficient', 'Missing Gap'],
                    datasets: [{
                        data: [100 - data.missing_percentage, data.missing_percentage],
                        backgroundColor: ['rgba(16, 185, 129, 0.8)', 'rgba(239, 68, 68, 0.8)'],
                        borderColor: '#0f172a',
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'bottom', labels: { color: '#f8fafc' } }
                    }
                }
            });
        });
});
