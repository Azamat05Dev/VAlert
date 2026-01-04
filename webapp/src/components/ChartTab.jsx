/**
 * ChartTab - Premium Interactive Charts with Multiple Types
 * Features: Line/Area/Bar charts, gradient fills, animations, zoom/pan
 */
import { useState, useEffect, useMemo, useRef } from 'react'
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    Title,
    Tooltip,
    Legend,
    Filler,
} from 'chart.js'
import { Line, Bar } from 'react-chartjs-2'
import zoomPlugin from 'chartjs-plugin-zoom'

// Register Chart.js components with zoom
ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    Title,
    Tooltip,
    Legend,
    Filler,
    zoomPlugin
)

// ==================== CONSTANTS ====================
const CURRENCIES = [
    { code: 'USD', name: 'Dollar', flag: '🇺🇸', color: '#22c55e', gradient: ['#22c55e', '#10b981'] },
    { code: 'EUR', name: 'Yevro', flag: '🇪🇺', color: '#3b82f6', gradient: ['#3b82f6', '#06b6d4'] },
    { code: 'RUB', name: 'Rubl', flag: '🇷🇺', color: '#ef4444', gradient: ['#ef4444', '#f97316'] },
    { code: 'GBP', name: 'Funt', flag: '🇬🇧', color: '#a855f7', gradient: ['#a855f7', '#ec4899'] },
    { code: 'CNY', name: 'Yuan', flag: '🇨🇳', color: '#f59e0b', gradient: ['#f59e0b', '#eab308'] },
]

const PERIODS = [
    { value: 7, label: '7 kun' },
    { value: 30, label: '30 kun' },
    { value: 90, label: '3 oy' },
]

const CHART_TYPES = [
    { value: 'area', label: 'Area', icon: '📈' },
    { value: 'line', label: 'Line', icon: '📉' },
    { value: 'bar', label: 'Bar', icon: '📊' },
]

const BASE_RATES = {
    USD: 12720,
    EUR: 13870,
    RUB: 128,
    GBP: 16180,
    CNY: 1752,
}

// ==================== HELPERS ====================
function generateHistory(currency, days) {
    const base = BASE_RATES[currency] || 12720
    const history = []
    let currentValue = base * (1 - 0.02)

    for (let i = days; i >= 0; i--) {
        const date = new Date()
        date.setDate(date.getDate() - i)
        const dailyChange = (Math.random() - 0.4) * 0.003
        currentValue *= (1 + dailyChange)

        history.push({
            date: date.toLocaleDateString('uz-UZ', { day: '2-digit', month: '2-digit' }),
            fullDate: date.toLocaleDateString('uz-UZ', { day: 'numeric', month: 'long' }),
            rate: Math.round(currentValue),
        })
    }
    return history
}

// Create gradient for chart
function createGradient(ctx, colors, height = 200) {
    const gradient = ctx.createLinearGradient(0, 0, 0, height)
    gradient.addColorStop(0, colors[0] + '60')
    gradient.addColorStop(0.5, colors[0] + '20')
    gradient.addColorStop(1, colors[0] + '00')
    return gradient
}

// ==================== COMPONENT ====================
export default function ChartTab() {
    const [currency, setCurrency] = useState('USD')
    const [period, setPeriod] = useState(7)
    const [chartType, setChartType] = useState('area')
    const [compareMode, setCompareMode] = useState(false)
    const [compareCurrencies, setCompareCurrencies] = useState(['USD', 'EUR'])
    const [history, setHistory] = useState([])
    const [loading, setLoading] = useState(true)
    const [animationKey, setAnimationKey] = useState(0)
    const [isZoomed, setIsZoomed] = useState(false)
    const chartRef = useRef(null)

    // Reset zoom function
    const resetZoom = () => {
        if (chartRef.current) {
            chartRef.current.resetZoom()
            setIsZoomed(false)
        }
    }

    // Fetch history data
    useEffect(() => {
        setLoading(true)
        setAnimationKey(prev => prev + 1)
        const timer = setTimeout(() => {
            if (compareMode) {
                const multiData = {}
                compareCurrencies.forEach(c => {
                    multiData[c] = generateHistory(c, period)
                })
                setHistory(multiData)
            } else {
                setHistory(generateHistory(currency, period))
            }
            setLoading(false)
        }, 400)

        return () => clearTimeout(timer)
    }, [currency, period, compareMode, compareCurrencies])

    // Calculate statistics
    const stats = useMemo(() => {
        if (!Array.isArray(history) || history.length < 2) return null

        const rates = history.map(h => h.rate)
        const min = Math.min(...rates)
        const max = Math.max(...rates)
        const avg = Math.round(rates.reduce((a, b) => a + b, 0) / rates.length)
        const first = rates[0]
        const last = rates[rates.length - 1]
        const change = ((last - first) / first * 100).toFixed(2)

        return { min, max, avg, change, first, last }
    }, [history])

    // Chart data configuration
    const chartData = useMemo(() => {
        if (compareMode && typeof history === 'object' && !Array.isArray(history)) {
            const firstCurrency = compareCurrencies[0]
            const labels = history[firstCurrency]?.map(h => h.date) || []

            return {
                labels,
                datasets: compareCurrencies.map(c => {
                    const currencyInfo = CURRENCIES.find(cur => cur.code === c)
                    return {
                        label: c,
                        data: history[c]?.map(h => h.rate) || [],
                        borderColor: currencyInfo?.color || '#0ea5e9',
                        backgroundColor: chartType === 'bar'
                            ? `${currencyInfo?.color || '#0ea5e9'}80`
                            : `${currencyInfo?.color || '#0ea5e9'}15`,
                        fill: chartType === 'area',
                        tension: 0.4,
                        pointRadius: 0,
                        pointHoverRadius: 6,
                        borderWidth: chartType === 'bar' ? 0 : 2,
                        borderRadius: chartType === 'bar' ? 8 : 0,
                    }
                }),
            }
        } else if (Array.isArray(history)) {
            const currencyInfo = CURRENCIES.find(c => c.code === currency)
            const ctx = chartRef.current?.ctx

            let bgColor = `${currencyInfo?.color || '#0ea5e9'}15`
            if (ctx && chartType === 'area' && currencyInfo?.gradient) {
                bgColor = createGradient(ctx, currencyInfo.gradient)
            } else if (chartType === 'bar') {
                bgColor = history.map((h, i, arr) => {
                    if (i === 0) return `${currencyInfo?.color}80`
                    return h.rate >= arr[i - 1].rate
                        ? 'rgba(34, 197, 94, 0.8)'
                        : 'rgba(239, 68, 68, 0.8)'
                })
            }

            return {
                labels: history.map(h => h.date),
                datasets: [{
                    label: `${currency}/UZS`,
                    data: history.map(h => h.rate),
                    borderColor: currencyInfo?.color || '#0ea5e9',
                    backgroundColor: bgColor,
                    fill: chartType === 'area',
                    tension: chartType === 'line' ? 0 : 0.4,
                    pointRadius: period <= 7 && chartType !== 'bar' ? 4 : 0,
                    pointHoverRadius: 6,
                    pointBackgroundColor: currencyInfo?.color || '#0ea5e9',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    borderWidth: chartType === 'bar' ? 0 : 3,
                    borderRadius: chartType === 'bar' ? 8 : 0,
                }],
            }
        }

        return { labels: [], datasets: [] }
    }, [history, currency, period, compareMode, compareCurrencies, chartType])

    // Chart options with animations
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
            duration: 800,
            easing: 'easeOutQuart',
        },
        transitions: {
            active: {
                animation: {
                    duration: 300,
                }
            }
        },
        interaction: {
            intersect: false,
            mode: 'index',
        },
        plugins: {
            legend: {
                display: compareMode,
                position: 'top',
                labels: {
                    color: '#94a3b8',
                    usePointStyle: true,
                    padding: 20,
                    font: { weight: 600 },
                },
            },
            tooltip: {
                backgroundColor: 'rgba(15, 23, 42, 0.95)',
                titleColor: '#f8fafc',
                bodyColor: '#94a3b8',
                borderColor: 'rgba(255, 255, 255, 0.1)',
                borderWidth: 1,
                padding: 16,
                cornerRadius: 12,
                displayColors: compareMode,
                titleFont: { size: 14, weight: 600 },
                bodyFont: { size: 13 },
                callbacks: {
                    label: (ctx) => ` ${ctx.dataset.label}: ${ctx.parsed.y.toLocaleString()} so'm`,
                    labelColor: (ctx) => ({
                        borderColor: ctx.dataset.borderColor,
                        backgroundColor: ctx.dataset.borderColor,
                        borderRadius: 4,
                    }),
                },
            },
            zoom: {
                pan: {
                    enabled: true,
                    mode: 'x',
                    threshold: 5,
                },
                zoom: {
                    wheel: {
                        enabled: true,
                        modifierKey: 'ctrl',
                    },
                    pinch: {
                        enabled: true,
                    },
                    mode: 'x',
                    onZoomComplete: () => setIsZoomed(true),
                },
                limits: {
                    x: { min: 'original', max: 'original' },
                },
            },
        },
        scales: {
            x: {
                grid: {
                    color: 'rgba(255, 255, 255, 0.03)',
                    drawBorder: false,
                },
                ticks: {
                    color: '#64748b',
                    maxTicksLimit: period <= 7 ? 7 : 5,
                    maxRotation: 0,
                    font: { size: 11 },
                },
            },
            y: {
                grid: {
                    color: 'rgba(255, 255, 255, 0.03)',
                    drawBorder: false,
                },
                ticks: {
                    color: '#64748b',
                    callback: (value) => value.toLocaleString(),
                    font: { size: 11 },
                },
            },
        },
    }

    // Toggle currency in compare mode
    const toggleCompareCurrency = (code) => {
        if (compareCurrencies.includes(code)) {
            if (compareCurrencies.length > 1) {
                setCompareCurrencies(prev => prev.filter(c => c !== code))
            }
        } else {
            if (compareCurrencies.length < 3) {
                setCompareCurrencies(prev => [...prev, code])
            }
        }
    }

    const ChartComponent = chartType === 'bar' ? Bar : Line

    return (
        <div className="space-y-4 animate-fade-in">
            {/* Mode Toggle & Chart Type */}
            <div className="glass-card">
                <div className="flex items-center justify-between mb-4">
                    <div>
                        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                            <span className="animate-heartbeat">📈</span> Kurs Grafigi
                        </h2>
                        <p className="text-sm text-dark-400">
                            {compareMode ? 'Taqqoslash rejimi' : 'Bitta valyuta'}
                        </p>
                    </div>
                    <button
                        onClick={() => setCompareMode(!compareMode)}
                        className={`px-4 py-2 rounded-lg font-medium transition-all glow-ring
              ${compareMode
                                ? 'bg-gradient-primary text-white shadow-glow'
                                : 'bg-dark-700/50 text-dark-400 hover:text-white'}`}
                    >
                        {compareMode ? '📊 Taqqoslash' : '📈 Oddiy'}
                    </button>
                </div>

                {/* Chart Type Selector */}
                <div className="flex gap-2">
                    {CHART_TYPES.map(type => (
                        <button
                            key={type.value}
                            onClick={() => setChartType(type.value)}
                            className={`flex-1 py-2.5 rounded-xl font-medium transition-all flex items-center justify-center gap-2
                ${chartType === type.value
                                    ? 'bg-gradient-to-r from-primary-500/20 to-cyan-500/20 text-white border border-primary-500/50'
                                    : 'bg-dark-800/50 text-dark-400 hover:text-white'}`}
                        >
                            <span>{type.icon}</span>
                            <span className="text-sm">{type.label}</span>
                        </button>
                    ))}
                </div>
            </div>

            {/* Currency Selector */}
            <div className="glass-card">
                <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
                    {CURRENCIES.map(cur => {
                        const isSelected = compareMode
                            ? compareCurrencies.includes(cur.code)
                            : currency === cur.code

                        return (
                            <button
                                key={cur.code}
                                onClick={() => compareMode ? toggleCompareCurrency(cur.code) : setCurrency(cur.code)}
                                className={`px-4 py-2.5 rounded-xl font-medium transition-all whitespace-nowrap flex items-center gap-2 card-3d
                  ${isSelected
                                        ? 'text-white shadow-lg scale-105'
                                        : 'bg-dark-700/50 text-dark-400 hover:text-white hover:scale-102'}`}
                                style={{
                                    background: isSelected ? `linear-gradient(135deg, ${cur.gradient[0]}30, ${cur.gradient[1]}30)` : undefined,
                                    borderColor: isSelected ? cur.color : 'transparent',
                                    borderWidth: 2,
                                    boxShadow: isSelected ? `0 0 20px ${cur.color}40` : undefined,
                                }}
                            >
                                <span className="text-lg">{cur.flag}</span>
                                <span>{cur.code}</span>
                            </button>
                        )
                    })}
                </div>
                {compareMode && (
                    <p className="text-xs text-dark-400 mt-2">
                        * 3 tagacha valyuta tanlash mumkin
                    </p>
                )}
            </div>

            {/* Period Selector */}
            <div className="flex gap-2">
                {PERIODS.map(p => (
                    <button
                        key={p.value}
                        onClick={() => setPeriod(p.value)}
                        className={`flex-1 py-2.5 rounded-xl font-medium transition-all duration-300
              ${period === p.value
                                ? 'bg-gradient-to-r from-dark-700 to-dark-600 text-white border border-dark-500 shadow-lg'
                                : 'bg-dark-800/50 text-dark-400 hover:text-white border border-transparent'}`}
                    >
                        {p.label}
                    </button>
                ))}
            </div>

            {/* Chart Card */}
            <div className="glass-card gradient-border p-0 overflow-hidden">
                <div className="p-5">
                    {/* Chart Header */}
                    {!compareMode && (
                        <div className="flex items-center justify-between mb-4">
                            <div>
                                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                                    {CURRENCIES.find(c => c.code === currency)?.flag}
                                    <span className="gradient-text">{currency}/UZS</span>
                                </h3>
                                <p className="text-sm text-dark-400">{period} kunlik grafik</p>
                            </div>
                            {stats && (
                                <div className={`px-4 py-2 rounded-full text-sm font-bold animate-scale-pop
                    ${parseFloat(stats.change) >= 0
                                        ? 'bg-gradient-to-r from-green-500/20 to-emerald-500/20 text-accent-green'
                                        : 'bg-gradient-to-r from-red-500/20 to-rose-500/20 text-accent-red'}`}>
                                    {parseFloat(stats.change) >= 0 ? '↑' : '↓'} {Math.abs(stats.change)}%
                                </div>
                            )}
                        </div>
                    )}

                    {/* Chart Container */}
                    <div className="h-72 relative" key={animationKey}>
                        {loading ? (
                            <div className="absolute inset-0 flex items-center justify-center">
                                <div className="spinner-premium"></div>
                            </div>
                        ) : (
                            <ChartComponent
                                ref={chartRef}
                                data={chartData}
                                options={chartOptions}
                            />
                        )}

                        {/* Reset Zoom Button */}
                        {isZoomed && !loading && (
                            <button
                                onClick={resetZoom}
                                className="absolute top-2 right-2 px-3 py-1.5 bg-dark-800/90 hover:bg-dark-700 
                                    text-sm text-white rounded-lg transition-all flex items-center gap-1.5
                                    border border-dark-600 shadow-lg animate-fade-in"
                            >
                                🔄 Reset Zoom
                            </button>
                        )}
                    </div>

                    {/* Zoom Hint */}
                    {!loading && !isZoomed && (
                        <p className="text-center text-xs text-dark-500 mt-2">
                            💡 Pinch yoki Ctrl + Scroll orqali zoom qiling
                        </p>
                    )}

                    {/* Statistics */}
                    {!loading && stats && !compareMode && (
                        <div className="grid grid-cols-4 gap-3 mt-6 pt-4 border-t border-dark-700/50">
                            <StatItem label="Min" value={stats.min.toLocaleString()} icon="📉" />
                            <StatItem label="Max" value={stats.max.toLocaleString()} icon="📈" />
                            <StatItem label="O'rtacha" value={stats.avg.toLocaleString()} icon="📊" />
                            <StatItem
                                label="O'zgarish"
                                value={`${parseFloat(stats.change) >= 0 ? '+' : ''}${stats.change}%`}
                                icon={parseFloat(stats.change) >= 0 ? '🟢' : '🔴'}
                                positive={parseFloat(stats.change) >= 0}
                            />
                        </div>
                    )}
                </div>
            </div>

            {/* Trend Analysis Card */}
            {!loading && stats && !compareMode && (
                <div className="glass-card card-3d">
                    <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
                        <span className="animate-heartbeat">📊</span> Trend Tahlili
                    </h3>
                    <div className="space-y-3">
                        <TrendItem
                            label={`${period} kunlik trend`}
                            value={parseFloat(stats.change) >= 0 ? 'Oshayapti' : 'Tushayapti'}
                            icon={parseFloat(stats.change) >= 0 ? '📈' : '📉'}
                            positive={parseFloat(stats.change) >= 0}
                        />
                        <TrendItem
                            label="Volatillik"
                            value={((stats.max - stats.min) / stats.avg * 100).toFixed(1) + '%'}
                            icon="📏"
                        />
                        <TrendItem
                            label="Tavsiya"
                            value={parseFloat(stats.change) >= 0
                                ? 'Sotish uchun kuting'
                                : 'Sotib olish vaqti'}
                            icon="💡"
                            highlight
                        />
                    </div>
                </div>
            )}
        </div>
    )
}

// Stat Item Component
function StatItem({ label, value, icon, positive }) {
    return (
        <div className="text-center p-3 bg-dark-800/30 rounded-xl">
            <p className="text-dark-400 text-xs mb-1 flex items-center justify-center gap-1">
                <span>{icon}</span> {label}
            </p>
            <p className={`font-bold text-lg ${positive !== undefined
                ? (positive ? 'text-accent-green' : 'text-accent-red')
                : 'text-white'
                }`}>
                {value}
            </p>
        </div>
    )
}

// Trend Item Component
function TrendItem({ label, value, icon, positive, highlight }) {
    return (
        <div className={`flex items-center justify-between p-4 rounded-xl transition-all
            ${highlight
                ? 'bg-gradient-to-r from-primary-500/10 to-cyan-500/10 border border-primary-500/30'
                : 'bg-dark-800/50 hover:bg-dark-700/50'}`}>
            <span className="text-dark-300 flex items-center gap-2">
                <span className={highlight ? 'animate-heartbeat' : ''}>{icon}</span> {label}
            </span>
            <span className={`font-semibold ${positive !== undefined
                ? (positive ? 'text-accent-green' : 'text-accent-red')
                : highlight ? 'text-primary-400' : 'text-white'
                }`}>
                {value}
            </span>
        </div>
    )
}
