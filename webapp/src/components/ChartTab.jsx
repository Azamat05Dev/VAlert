/**
 * ChartTab - Interactive currency charts with Chart.js
 */
import { useState, useEffect } from 'react';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler
);

const CURRENCIES = ['USD', 'EUR', 'RUB', 'GBP', 'CNY'];
const PERIODS = [
    { label: '7 kun', value: 7 },
    { label: '30 kun', value: 30 },
];

// Generate mock history data
function generateHistory(currency, days) {
    const baseRates = { USD: 12720, EUR: 13870, RUB: 128, GBP: 16180, CNY: 1752 };
    const base = baseRates[currency] || 12720;
    const history = [];

    for (let i = days; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        const variation = Math.sin(i / 3) * 0.01 + (Math.random() - 0.5) * 0.005;
        history.push({
            date: date.toLocaleDateString('uz-UZ', { day: '2-digit', month: '2-digit' }),
            rate: Math.round(base * (1 + variation)),
        });
    }

    return history;
}

export default function ChartTab() {
    const [currency, setCurrency] = useState('USD');
    const [period, setPeriod] = useState(7);
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        setLoading(true);
        // Simulate API call
        setTimeout(() => {
            setHistory(generateHistory(currency, period));
            setLoading(false);
        }, 500);
    }, [currency, period]);

    const chartData = {
        labels: history.map(h => h.date),
        datasets: [
            {
                label: `${currency}/UZS`,
                data: history.map(h => h.rate),
                borderColor: '#0ea5e9',
                backgroundColor: 'rgba(14, 165, 233, 0.1)',
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointBackgroundColor: '#0ea5e9',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
            },
        ],
    };

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false,
            },
            tooltip: {
                backgroundColor: 'rgba(15, 23, 42, 0.9)',
                titleColor: '#f8fafc',
                bodyColor: '#94a3b8',
                borderColor: 'rgba(255, 255, 255, 0.1)',
                borderWidth: 1,
                padding: 12,
                cornerRadius: 8,
                displayColors: false,
                callbacks: {
                    label: (ctx) => `${ctx.parsed.y.toLocaleString()} so'm`,
                },
            },
        },
        scales: {
            x: {
                grid: {
                    color: 'rgba(255, 255, 255, 0.05)',
                },
                ticks: {
                    color: '#64748b',
                    maxTicksLimit: 7,
                },
            },
            y: {
                grid: {
                    color: 'rgba(255, 255, 255, 0.05)',
                },
                ticks: {
                    color: '#64748b',
                    callback: (value) => value.toLocaleString(),
                },
            },
        },
        interaction: {
            intersect: false,
            mode: 'index',
        },
    };

    // Calculate trend
    const trend = history.length >= 2
        ? ((history[history.length - 1]?.rate - history[0]?.rate) / history[0]?.rate * 100).toFixed(2)
        : 0;
    const isUp = parseFloat(trend) >= 0;

    return (
        <div className="space-y-4 animate-slide-up">
            {/* Currency Selector */}
            <div className="glass-card">
                <div className="flex gap-2 overflow-x-auto pb-2">
                    {CURRENCIES.map(cur => (
                        <button
                            key={cur}
                            onClick={() => setCurrency(cur)}
                            className={`px-4 py-2 rounded-lg font-medium transition-all whitespace-nowrap
                ${currency === cur
                                    ? 'bg-primary-500 text-white shadow-glow'
                                    : 'bg-dark-700/50 text-dark-400 hover:text-white'}`}
                        >
                            {cur}
                        </button>
                    ))}
                </div>
            </div>

            {/* Period Selector */}
            <div className="flex gap-2">
                {PERIODS.map(p => (
                    <button
                        key={p.value}
                        onClick={() => setPeriod(p.value)}
                        className={`flex-1 py-2 rounded-lg font-medium transition-all
              ${period === p.value
                                ? 'bg-dark-700 text-white border border-dark-500'
                                : 'bg-dark-800/50 text-dark-400 hover:text-white border border-transparent'}`}
                    >
                        {p.label}
                    </button>
                ))}
            </div>

            {/* Chart Card */}
            <div className="glass-card">
                <div className="flex items-center justify-between mb-4">
                    <div>
                        <h2 className="text-xl font-bold text-white flex items-center gap-2">
                            📈 {currency}/UZS
                        </h2>
                        <p className="text-sm text-dark-400">{period} kunlik grafik</p>
                    </div>
                    <div className={`px-3 py-1 rounded-full text-sm font-semibold
            ${isUp ? 'bg-accent-green/20 text-accent-green' : 'bg-accent-red/20 text-accent-red'}`}>
                        {isUp ? '↑' : '↓'} {Math.abs(trend)}%
                    </div>
                </div>

                {/* Chart */}
                <div className="h-64 relative">
                    {loading ? (
                        <div className="absolute inset-0 flex items-center justify-center">
                            <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin"></div>
                        </div>
                    ) : (
                        <Line data={chartData} options={chartOptions} />
                    )}
                </div>

                {/* Stats */}
                {!loading && history.length > 0 && (
                    <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t border-dark-700">
                        <div className="text-center">
                            <p className="text-dark-400 text-xs">Boshlang'ich</p>
                            <p className="text-white font-semibold">{history[0]?.rate?.toLocaleString()}</p>
                        </div>
                        <div className="text-center">
                            <p className="text-dark-400 text-xs">Hozir</p>
                            <p className="text-white font-semibold">{history[history.length - 1]?.rate?.toLocaleString()}</p>
                        </div>
                        <div className="text-center">
                            <p className="text-dark-400 text-xs">O'zgarish</p>
                            <p className={`font-semibold ${isUp ? 'text-accent-green' : 'text-accent-red'}`}>
                                {isUp ? '+' : ''}{trend}%
                            </p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
