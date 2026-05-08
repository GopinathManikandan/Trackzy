/**
 * Charts and Data Visualization for Department Attendance Management System
 * Uses Chart.js for creating interactive charts and graphs
 */

const AttendanceCharts = {
    // Chart configuration defaults
    defaultOptions: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
                labels: {
                    usePointStyle: true,
                    padding: 20,
                    font: {
                        family: 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif',
                        size: 12
                    }
                }
            },
            tooltip: {
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                titleColor: 'white',
                bodyColor: 'white',
                borderColor: '#0d6efd',
                borderWidth: 1,
                cornerRadius: 8,
                padding: 12,
                displayColors: false
            }
        },
        scales: {
            x: {
                grid: {
                    display: true,
                    color: 'rgba(0, 0, 0, 0.1)'
                },
                ticks: {
                    font: {
                        family: 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif',
                        size: 11
                    }
                }
            },
            y: {
                grid: {
                    display: true,
                    color: 'rgba(0, 0, 0, 0.1)'
                },
                ticks: {
                    font: {
                        family: 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif',
                        size: 11
                    }
                }
            }
        }
    },

    // Color schemes
    colorSchemes: {
        primary: ['#0d6efd', '#6610f2', '#6f42c1', '#d63384', '#dc3545', '#fd7e14', '#ffc107', '#198754'],
        attendance: {
            present: '#198754',
            absent: '#dc3545',
            late: '#ffc107'
        },
        performance: {
            excellent: '#198754',
            good: '#17a2b8',
            average: '#ffc107',
            poor: '#dc3545'
        }
    },

    // Initialize all charts
    init() {
        
        this.initStudentPerformanceChart();
        this.bindChartEvents();
    },

    // Create attendance trend line chart
    createAttendanceTrendChart(canvasId, data, options = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;

        const ctx = canvas.getContext('2d');
        
        const config = {
            type: 'line',
            data: {
                labels: data.labels || [],
                datasets: [{
                    label: 'Attendance %',
                    data: data.values || [],
                    borderColor: this.colorSchemes.primary[0],
                    backgroundColor: `${this.colorSchemes.primary[0]}20`,
                    borderWidth: 3,
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: this.colorSchemes.primary[0],
                    pointBorderColor: 'white',
                    pointBorderWidth: 2,
                    pointRadius: 6,
                    pointHoverRadius: 8
                }]
            },
            options: {
                ...this.defaultOptions,
                scales: {
                    ...this.defaultOptions.scales,
                    y: {
                        ...this.defaultOptions.scales.y,
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            ...this.defaultOptions.scales.y.ticks,
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                },
                plugins: {
                    ...this.defaultOptions.plugins,
                    tooltip: {
                        ...this.defaultOptions.plugins.tooltip,
                        callbacks: {
                            label: function(context) {
                                return `Attendance: ${context.parsed.y.toFixed(1)}%`;
                            }
                        }
                    }
                },
                ...options
            }
        };

        return new Chart(ctx, config);
    },

    // Create bar chart for class comparison
    createClassComparisonChart(canvasId, data, options = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;

        const ctx = canvas.getContext('2d');

        // Color code based on performance
        const backgroundColors = data.values.map(value => {
            if (value >= 90) return this.colorSchemes.performance.excellent;
            if (value >= 75) return this.colorSchemes.performance.good;
            if (value >= 60) return this.colorSchemes.performance.average;
            return this.colorSchemes.performance.poor;
        });

        const config = {
            type: 'bar',
            data: {
                labels: data.labels || [],
                datasets: [{
                    label: 'Attendance %',
                    data: data.values || [],
                    backgroundColor: backgroundColors,
                    borderColor: backgroundColors.map(color => color.replace('0.8', '1')),
                    borderWidth: 1,
                    borderRadius: 6,
                    borderSkipped: false
                }]
            },
            options: {
                ...this.defaultOptions,
                scales: {
                    ...this.defaultOptions.scales,
                    y: {
                        ...this.defaultOptions.scales.y,
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            ...this.defaultOptions.scales.y.ticks,
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                },
                plugins: {
                    ...this.defaultOptions.plugins,
                    legend: {
                        display: false
                    },
                    tooltip: {
                        ...this.defaultOptions.plugins.tooltip,
                        callbacks: {
                            label: function(context) {
                                const value = context.parsed.y;
                                let status = 'Poor';
                                if (value >= 90) status = 'Excellent';
                                else if (value >= 75) status = 'Good';
                                else if (value >= 60) status = 'Average';
                                
                                return [`Attendance: ${value.toFixed(1)}%`, `Status: ${status}`];
                            }
                        }
                    }
                },
                ...options
            }
        };

        return new Chart(ctx, config);
    },

    // Create doughnut chart for attendance breakdown
    createAttendanceBreakdownChart(canvasId, data, options = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;

        const ctx = canvas.getContext('2d');

        const config = {
            type: 'doughnut',
            data: {
                labels: ['Present', 'Absent', 'Late'],
                datasets: [{
                    data: [
                        data.present || 0,
                        data.absent || 0,
                        data.late || 0
                    ],
                    backgroundColor: [
                        this.colorSchemes.attendance.present,
                        this.colorSchemes.attendance.absent,
                        this.colorSchemes.attendance.late
                    ],
                    borderWidth: 0,
                    cutout: '60%'
                }]
            },
            options: {
                ...this.defaultOptions,
                plugins: {
                    ...this.defaultOptions.plugins,
                    legend: {
                        position: 'bottom',
                        labels: {
                            ...this.defaultOptions.plugins.legend.labels,
                            generateLabels: function(chart) {
                                const data = chart.data;
                                if (data.labels.length && data.datasets.length) {
                                    const dataset = data.datasets[0];
                                    const total = dataset.data.reduce((a, b) => a + b, 0);
                                    
                                    return data.labels.map((label, i) => {
                                        const value = dataset.data[i];
                                        const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : '0';
                                        
                                        return {
                                            text: `${label}: ${value} (${percentage}%)`,
                                            fillStyle: dataset.backgroundColor[i],
                                            hidden: false,
                                            index: i
                                        };
                                    });
                                }
                                return [];
                            }
                        }
                    },
                    tooltip: {
                        ...this.defaultOptions.plugins.tooltip,
                        callbacks: {
                            label: function(context) {
                                const label = context.label;
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : '0';
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                },
                ...options
            }
        };

        return new Chart(ctx, config);
    },

    // Create mixed chart for detailed analysis
    createMixedAnalysisChart(canvasId, data, options = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;

        const ctx = canvas.getContext('2d');

        const config = {
            type: 'bar',
            data: {
                labels: data.labels || [],
                datasets: [
                    {
                        type: 'bar',
                        label: 'Present',
                        data: data.present || [],
                        backgroundColor: this.colorSchemes.attendance.present + '80',
                        borderColor: this.colorSchemes.attendance.present,
                        borderWidth: 1
                    },
                    {
                        type: 'bar',
                        label: 'Absent',
                        data: data.absent || [],
                        backgroundColor: this.colorSchemes.attendance.absent + '80',
                        borderColor: this.colorSchemes.attendance.absent,
                        borderWidth: 1
                    },
                    {
                        type: 'line',
                        label: 'Attendance %',
                        data: data.percentage || [],
                        borderColor: this.colorSchemes.primary[1],
                        backgroundColor: this.colorSchemes.primary[1] + '20',
                        borderWidth: 3,
                        tension: 0.4,
                        fill: false,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                ...this.defaultOptions,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                scales: {
                    x: this.defaultOptions.scales.x,
                    y: {
                        ...this.defaultOptions.scales.y,
                        type: 'linear',
                        display: true,
                        position: 'left',
                        beginAtZero: true
                    },
                    y1: {
                        ...this.defaultOptions.scales.y,
                        type: 'linear',
                        display: true,
                        position: 'right',
                        beginAtZero: true,
                        max: 100,
                        grid: {
                            drawOnChartArea: false
                        },
                        ticks: {
                            ...this.defaultOptions.scales.y.ticks,
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                },
                ...options
            }
        };

        return new Chart(ctx, config);
    },

    

    

    

    // Initialize student performance chart
    initStudentPerformanceChart() {
        const performanceCanvas = document.getElementById('studentPerformanceChart');
        if (performanceCanvas && window.studentPerformanceData) {
            this.createMixedAnalysisChart('studentPerformanceChart', window.studentPerformanceData);
        }
    },

    // Bind chart-related events
    bindChartEvents() {
        // Chart export functionality
        document.querySelectorAll('[data-chart-export]').forEach(button => {
            button.addEventListener('click', (e) => {
                const chartId = e.target.getAttribute('data-chart-export');
                this.exportChart(chartId);
            });
        });

        // Chart period toggle
        document.querySelectorAll('[data-chart-period]').forEach(button => {
            button.addEventListener('click', (e) => {
                const period = e.target.getAttribute('data-chart-period');
                const chartId = e.target.getAttribute('data-chart-id');
                this.updateChartPeriod(chartId, period);
            });
        });

        // Chart type toggle
        document.querySelectorAll('[data-chart-type]').forEach(button => {
            button.addEventListener('click', (e) => {
                const type = e.target.getAttribute('data-chart-type');
                const chartId = e.target.getAttribute('data-chart-id');
                this.changeChartType(chartId, type);
            });
        });
    },

    // Export chart as image
    exportChart(chartId, filename) {
        const canvas = document.getElementById(chartId);
        if (!canvas) return;

        const link = document.createElement('a');
        link.download = filename || `${chartId}.png`;
        link.href = canvas.toDataURL('image/png');
        link.click();

        AttendanceApp.utils.showToast('Chart exported successfully!', 'success');
    },

    // Update chart data for different periods
    updateChartPeriod(chartId, period) {
        // This would typically fetch new data from the server
        // For now, we'll simulate the update
        console.log(`Updating chart ${chartId} for period: ${period}`);
        AttendanceApp.utils.showToast(`Chart updated for ${period} period`, 'info');
    },

    // Change chart type dynamically
    changeChartType(chartId, newType) {
        const canvas = document.getElementById(chartId);
        if (!canvas) return;

        // Get the existing chart instance
        const existingChart = Chart.getChart(canvas);
        if (existingChart) {
            const currentData = existingChart.data;
            existingChart.destroy();

            // Create new chart with same data but different type
            const ctx = canvas.getContext('2d');
            new Chart(ctx, {
                type: newType,
                data: currentData,
                options: this.defaultOptions
            });

            AttendanceApp.utils.showToast(`Chart type changed to ${newType}`, 'success');
        }
    },

    // Create real-time updating chart
    createRealTimeChart(canvasId, updateCallback) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;

        const ctx = canvas.getContext('2d');
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Real-time Data',
                    data: [],
                    borderColor: this.colorSchemes.primary[0],
                    backgroundColor: this.colorSchemes.primary[0] + '20',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                ...this.defaultOptions,
                scales: {
                    ...this.defaultOptions.scales,
                    x: {
                        ...this.defaultOptions.scales.x,
                        type: 'realtime',
                        realtime: {
                            duration: 20000,
                            refresh: 1000,
                            delay: 1000,
                            onRefresh: updateCallback
                        }
                    }
                }
            }
        });

        return chart;
    },

    // Utility function to generate chart colors
    generateColors(count, alpha = 0.8) {
        const colors = [];
        for (let i = 0; i < count; i++) {
            const hue = (i * 360 / count) % 360;
            colors.push(`hsla(${hue}, 70%, 50%, ${alpha})`);
        }
        return colors;
    },

    // Create gradient for charts
    createGradient(ctx, color1, color2) {
        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, color1);
        gradient.addColorStop(1, color2);
        return gradient;
    },

    // Animate chart on load
    animateChart(chartInstance, duration = 1000) {
        if (!chartInstance) return;

        chartInstance.options.animation = {
            duration: duration,
            easing: 'easeInOutQuart'
        };

        chartInstance.update('active');
    },

    // Get chart performance metrics
    getChartMetrics(chartInstance) {
        if (!chartInstance || !chartInstance.data) return null;

        const datasets = chartInstance.data.datasets;
        if (!datasets || datasets.length === 0) return null;

        const data = datasets[0].data;
        if (!data || data.length === 0) return null;

        const total = data.reduce((sum, value) => sum + value, 0);
        const average = total / data.length;
        const max = Math.max(...data);
        const min = Math.min(...data);

        return {
            total,
            average: parseFloat(average.toFixed(2)),
            max,
            min,
            count: data.length
        };
    }
};

// Initialize charts when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    AttendanceCharts.init();
});

// Global chart utilities
window.AttendanceCharts = AttendanceCharts;

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AttendanceCharts;
}
