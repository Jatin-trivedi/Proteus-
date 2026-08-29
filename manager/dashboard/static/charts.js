// Real-time agent status chart (optional)
document.addEventListener('DOMContentLoaded', function() {
    const ctx = document.getElementById('agentChart');
    if (!ctx) return;
    const chart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Online', 'Offline'],
            datasets: [{
                data: [0, 0],
                backgroundColor: ['#28a745', '#6c757d']
            }]
        },
        options: { responsive: true }
    });

    function updateChart() {
        fetch('/api/v1/agent/list')
            .then(r => r.json())
            .then(agents => {
                const online = agents.filter(a => a.status === 'online').length;
                const offline = agents.length - online;
                chart.data.datasets[0].data = [online, offline];
                chart.update();
            });
    }

    updateChart();
    setInterval(updateChart, 10000);
});