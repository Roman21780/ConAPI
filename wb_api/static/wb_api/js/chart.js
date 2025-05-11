// Глобальные настройки Chart.js
Chart.defaults.font.family = 'Roboto, sans-serif';
Chart.defaults.color = '#333';
Chart.defaults.borderColor = 'rgba(0, 0, 0, 0.1)';

// Функция для создания графика цен
function createPriceChart(ctx, products) {
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: products.map(p => p.name.substring(0, 20) + (p.name.length > 20 ? '...' : '')),
            datasets: [{
                label: 'Цена',
                data: products.map(p => p.prices[0].price),
                backgroundColor: 'rgba(54, 162, 235, 0.7)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Цена: ${context.raw} ₽`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Цена (₽)'
                    }
                }
            }
        }
    });
}

// Функция для создания графика остатков
function createStockChart(ctx, products) {
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: products.map(p => p.name.substring(0, 20) + (p.name.length > 20 ? '...' : '')),
            datasets: [{
                label: 'Общие остатки',
                data: products.map(p => p.stocks.reduce((sum, s) => sum + s.amount, 0)),
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 2,
                tension: 0.1,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Остатки: ${context.raw} шт.`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Остатки (шт.)'
                    }
                }
            }
        }
    });
}