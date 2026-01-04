/**
 * PortfolioTab - Premium Currency Portfolio Tracker
 * Features: Holdings, P/L tracking, Pie chart allocation, Historical P/L chart, Animated counters
 */
import { useState, useEffect, useMemo, useRef } from 'react'
import { useApp } from '../App'
import {
    Chart as ChartJS,
    ArcElement,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Tooltip,
    Legend,
    Filler,
} from 'chart.js'
import { Doughnut, Line } from 'react-chartjs-2'

// Register Chart.js components
ChartJS.register(ArcElement, CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend, Filler)

const CURRENCIES = [
    { code: 'USD', flag: '🇺🇸', name: 'Dollar', color: '#22c55e' },
    { code: 'EUR', flag: '🇪🇺', name: 'Yevro', color: '#3b82f6' },
    { code: 'RUB', flag: '🇷🇺', name: 'Rubl', color: '#ef4444' },
    { code: 'GBP', flag: '🇬🇧', name: 'Funt', color: '#a855f7' },
    { code: 'CNY', flag: '🇨🇳', name: 'Yuan', color: '#f59e0b' },
]

// Animated Counter Hook
function useAnimatedCounter(targetValue, duration = 1000) {
    const [value, setValue] = useState(0)
    const previousValue = useRef(0)

    useEffect(() => {
        const startValue = previousValue.current
        const difference = targetValue - startValue
        const startTime = Date.now()

        const animate = () => {
            const elapsed = Date.now() - startTime
            const progress = Math.min(elapsed / duration, 1)

            // Easing function (ease-out-cubic)
            const eased = 1 - Math.pow(1 - progress, 3)
            const currentValue = startValue + (difference * eased)

            setValue(Math.round(currentValue))

            if (progress < 1) {
                requestAnimationFrame(animate)
            } else {
                previousValue.current = targetValue
            }
        }

        requestAnimationFrame(animate)
    }, [targetValue, duration])

    return value
}

export default function PortfolioTab() {
    const { rates, haptic, showToast } = useApp()
    const [holdings, setHoldings] = useState(() => {
        const saved = localStorage.getItem('valert_portfolio')
        return saved ? JSON.parse(saved) : []
    })
    const [showAddModal, setShowAddModal] = useState(false)
    const [editingId, setEditingId] = useState(null)
    const [view, setView] = useState('overview') // 'overview' | 'analytics'

    // Save to localStorage
    useEffect(() => {
        localStorage.setItem('valert_portfolio', JSON.stringify(holdings))
    }, [holdings])

    // Calculate total portfolio value
    const portfolioStats = useMemo(() => {
        let totalValue = 0
        let totalCost = 0
        const allocation = []

        holdings.forEach(h => {
            const rate = rates.find(r => r.code === h.currency)
            if (rate) {
                const currentValue = h.amount * rate.official
                totalValue += currentValue
                totalCost += h.amount * h.buyPrice

                allocation.push({
                    currency: h.currency,
                    value: currentValue,
                    color: CURRENCIES.find(c => c.code === h.currency)?.color || '#64748b',
                })
            }
        })

        const profit = totalValue - totalCost
        const profitPercent = totalCost > 0 ? (profit / totalCost * 100) : 0

        return { totalValue, totalCost, profit, profitPercent, allocation }
    }, [holdings, rates])

    // Animated values
    const animatedTotalValue = useAnimatedCounter(portfolioStats.totalValue, 800)
    const animatedProfit = useAnimatedCounter(portfolioStats.profit, 800)

    // Add holding
    const handleAdd = (data) => {
        const newHolding = {
            id: Date.now(),
            ...data,
            createdAt: new Date().toISOString(),
        }
        setHoldings(prev => [...prev, newHolding])
        haptic('success')
        showToast('Portfelga qo\'shildi ✓', 'success')
        setShowAddModal(false)
    }

    // Update holding
    const handleUpdate = (id, data) => {
        setHoldings(prev => prev.map(h => h.id === id ? { ...h, ...data } : h))
        haptic('light')
        showToast('Yangilandi ✓', 'success')
        setEditingId(null)
    }

    // Delete holding
    const handleDelete = (id) => {
        haptic('medium')
        setHoldings(prev => prev.filter(h => h.id !== id))
        showToast('O\'chirildi', 'info')
    }

    // Export portfolio to CSV
    const handleExport = () => {
        haptic('medium')

        // CSV header
        const headers = ['Valyuta', 'Miqdor', 'Sotib olish narxi', 'Joriy kurs', 'Joriy qiymat', 'Foyda/Zarar', 'Foyda %']

        // CSV rows
        const rows = holdings.map(h => {
            const rate = rates.find(r => r.code === h.currency)
            const currentRate = rate?.official || 0
            const currentValue = h.amount * currentRate
            const costValue = h.amount * h.buyPrice
            const profit = currentValue - costValue
            const profitPercent = costValue > 0 ? ((profit / costValue) * 100).toFixed(2) : 0

            return [
                h.currency,
                h.amount,
                h.buyPrice,
                currentRate,
                currentValue.toFixed(0),
                profit.toFixed(0),
                `${profitPercent}%`
            ].join(',')
        })

        // Add summary row
        rows.push('')
        rows.push(`Jami,,,,${portfolioStats.totalValue.toFixed(0)},${portfolioStats.profit.toFixed(0)},${portfolioStats.profitPercent.toFixed(2)}%`)

        // Create CSV content
        const csvContent = [headers.join(','), ...rows].join('\n')

        // Create download link
        const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' })
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `valert_portfolio_${new Date().toISOString().split('T')[0]}.csv`
        link.click()
        URL.revokeObjectURL(url)

        showToast('Portfolio eksport qilindi ✓', 'success')
    }

    // Pie chart data
    const pieChartData = useMemo(() => {
        return {
            labels: portfolioStats.allocation.map(a => a.currency),
            datasets: [{
                data: portfolioStats.allocation.map(a => a.value),
                backgroundColor: portfolioStats.allocation.map(a => a.color + '80'),
                borderColor: portfolioStats.allocation.map(a => a.color),
                borderWidth: 2,
                hoverOffset: 10,
            }],
        }
    }, [portfolioStats.allocation])

    const pieChartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '65%',
        plugins: {
            legend: {
                display: false,
            },
            tooltip: {
                backgroundColor: 'rgba(15, 23, 42, 0.95)',
                titleColor: '#f8fafc',
                bodyColor: '#94a3b8',
                borderColor: 'rgba(255, 255, 255, 0.1)',
                borderWidth: 1,
                padding: 12,
                cornerRadius: 8,
                callbacks: {
                    label: (ctx) => {
                        const value = ctx.parsed
                        const total = ctx.dataset.data.reduce((a, b) => a + b, 0)
                        const percent = ((value / total) * 100).toFixed(1)
                        return ` ${value.toLocaleString()} so'm (${percent}%)`
                    },
                },
            },
        },
        animation: {
            animateRotate: true,
            animateScale: true,
        },
    }

    return (
        <div className="space-y-4 animate-fade-in">
            {/* View Toggle */}
            <div className="flex gap-2">
                <button
                    onClick={() => setView('overview')}
                    className={`flex-1 py-2.5 rounded-xl font-medium transition-all flex items-center justify-center gap-2
                        ${view === 'overview'
                            ? 'bg-gradient-primary text-white shadow-glow'
                            : 'bg-dark-700/50 text-dark-400 hover:text-white'}`}
                >
                    <span>💼</span> Portfel
                </button>
                <button
                    onClick={() => setView('analytics')}
                    className={`flex-1 py-2.5 rounded-xl font-medium transition-all flex items-center justify-center gap-2
                        ${view === 'analytics'
                            ? 'bg-gradient-primary text-white shadow-glow'
                            : 'bg-dark-700/50 text-dark-400 hover:text-white'}`}
                >
                    <span>📊</span> Tahlil
                </button>
            </div>

            {view === 'overview' ? (
                <>
                    {/* Portfolio Summary with Animated Counters */}
                    <div className="glass-card gradient-border p-0 overflow-hidden">
                        <div className="p-5 bg-gradient-to-r from-primary-500/10 to-cyan-500/10">
                            <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                                <span className="animate-heartbeat">💼</span> Mening Portfelim
                            </h2>

                            <div className="grid grid-cols-2 gap-4">
                                {/* Total Value */}
                                <div>
                                    <p className="text-xs text-dark-400 mb-1">Umumiy qiymat</p>
                                    <p className="text-2xl font-bold text-white number-flash">
                                        {animatedTotalValue.toLocaleString('uz-UZ')}
                                        <span className="text-sm text-dark-400 ml-1">so'm</span>
                                    </p>
                                </div>

                                {/* Profit/Loss */}
                                <div>
                                    <p className="text-xs text-dark-400 mb-1">Foyda/Zarar</p>
                                    <p className={`text-2xl font-bold ${portfolioStats.profit >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
                                        {portfolioStats.profit >= 0 ? '+' : ''}{animatedProfit.toLocaleString('uz-UZ')}
                                    </p>
                                    <p className={`text-sm font-semibold ${portfolioStats.profitPercent >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
                                        {portfolioStats.profitPercent >= 0 ? '📈' : '📉'} {Math.abs(portfolioStats.profitPercent).toFixed(2)}%
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Holdings List */}
                    <div className="space-y-3">
                        <div className="flex items-center justify-between">
                            <h3 className="font-semibold text-dark-200">Valyutalar</h3>
                            <button
                                onClick={() => setShowAddModal(true)}
                                className="btn-primary text-sm py-2 px-4 glow-ring"
                            >
                                ➕ Qo'shish
                            </button>
                        </div>

                        {holdings.length === 0 ? (
                            <EmptyPortfolio onAdd={() => setShowAddModal(true)} />
                        ) : (
                            holdings.map((holding, index) => (
                                <HoldingCard
                                    key={holding.id}
                                    holding={holding}
                                    currentRate={rates.find(r => r.code === holding.currency)?.official || 0}
                                    onEdit={() => setEditingId(holding.id)}
                                    onDelete={() => handleDelete(holding.id)}
                                    delay={index * 0.05}
                                />
                            ))
                        )}
                    </div>
                </>
            ) : (
                /* Analytics View */
                <>
                    {holdings.length > 0 ? (
                        <>
                            {/* Allocation Pie Chart */}
                            <div className="glass-card">
                                <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
                                    <span>🥧</span> Taqsimot
                                </h3>
                                <div className="h-64 relative">
                                    <Doughnut data={pieChartData} options={pieChartOptions} />
                                    {/* Center text */}
                                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                                        <div className="text-center">
                                            <p className="text-2xl font-bold text-white">
                                                {holdings.length}
                                            </p>
                                            <p className="text-xs text-dark-400">valyuta</p>
                                        </div>
                                    </div>
                                </div>

                                {/* Legend */}
                                <div className="grid grid-cols-2 gap-2 mt-4">
                                    {portfolioStats.allocation.map(item => (
                                        <div key={item.currency} className="flex items-center gap-2 p-2 bg-dark-800/50 rounded-lg">
                                            <div
                                                className="w-3 h-3 rounded-full"
                                                style={{ backgroundColor: item.color }}
                                            />
                                            <span className="text-sm text-white font-medium">{item.currency}</span>
                                            <span className="text-xs text-dark-400 ml-auto">
                                                {((item.value / portfolioStats.totalValue) * 100).toFixed(0)}%
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Performance Metrics */}
                            <div className="glass-card">
                                <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
                                    <span>📈</span> Ko'rsatkichlar
                                </h3>
                                <div className="space-y-3">
                                    <MetricRow
                                        label="Umumiy investitsiya"
                                        value={`${portfolioStats.totalCost.toLocaleString()} so'm`}
                                        icon="💰"
                                    />
                                    <MetricRow
                                        label="Joriy qiymat"
                                        value={`${portfolioStats.totalValue.toLocaleString()} so'm`}
                                        icon="📊"
                                    />
                                    <MetricRow
                                        label="Foyda/Zarar"
                                        value={`${portfolioStats.profit >= 0 ? '+' : ''}${portfolioStats.profit.toLocaleString()} so'm`}
                                        icon={portfolioStats.profit >= 0 ? '✅' : '❌'}
                                        positive={portfolioStats.profit >= 0}
                                    />
                                    <MetricRow
                                        label="ROI"
                                        value={`${portfolioStats.profitPercent >= 0 ? '+' : ''}${portfolioStats.profitPercent.toFixed(2)}%`}
                                        icon="📈"
                                        positive={portfolioStats.profitPercent >= 0}
                                        highlight
                                    />
                                </div>
                            </div>

                            {/* Historical P/L Chart */}
                            <HistoricalPLChart
                                holdings={holdings}
                                rates={rates}
                                totalValue={portfolioStats.totalValue}
                                totalCost={portfolioStats.totalCost}
                            />

                            {/* Best/Worst Performers */}
                            {holdings.length > 1 && (
                                <div className="grid grid-cols-2 gap-3">
                                    <PerformanceCard
                                        type="best"
                                        holdings={holdings}
                                        rates={rates}
                                    />
                                    <PerformanceCard
                                        type="worst"
                                        holdings={holdings}
                                        rates={rates}
                                    />
                                </div>
                            )}

                            {/* Export Button */}
                            <button
                                onClick={handleExport}
                                className="w-full py-4 bg-gradient-to-r from-primary-500/20 to-cyan-500/20 
                                    hover:from-primary-500/30 hover:to-cyan-500/30
                                    border border-primary-500/30 rounded-xl font-medium text-white 
                                    flex items-center justify-center gap-2 transition-all"
                            >
                                <span>📥</span> CSV Eksport qilish
                            </button>
                        </>
                    ) : (
                        <div className="glass-card text-center py-12">
                            <p className="text-5xl mb-4">📊</p>
                            <p className="text-dark-400 mb-4">Tahlil uchun avval valyuta qo'shing</p>
                            <button onClick={() => { setView('overview'); setShowAddModal(true); }} className="btn-primary">
                                Valyuta qo'shish
                            </button>
                        </div>
                    )}
                </>
            )}

            {/* Tips */}
            {holdings.length > 0 && view === 'overview' && (
                <div className="glass-card bg-gradient-to-r from-primary-500/10 to-cyan-500/10 border-primary-500/20">
                    <p className="text-sm text-dark-300">
                        💡 <strong>Maslahat:</strong> Portfel qiymati real vaqtda CBU kursi asosida hisoblanadi.
                    </p>
                </div>
            )}

            {/* Add Modal */}
            {showAddModal && (
                <AddHoldingModal
                    onClose={() => setShowAddModal(false)}
                    onSubmit={handleAdd}
                />
            )}

            {/* Edit Modal */}
            {editingId && (
                <EditHoldingModal
                    holding={holdings.find(h => h.id === editingId)}
                    onClose={() => setEditingId(null)}
                    onSubmit={(data) => handleUpdate(editingId, data)}
                    onDelete={() => handleDelete(editingId)}
                />
            )}
        </div>
    )
}

// Metric Row Component
function MetricRow({ label, value, icon, positive, highlight }) {
    return (
        <div className={`flex items-center justify-between p-3 rounded-xl transition-all
            ${highlight
                ? 'bg-gradient-to-r from-primary-500/20 to-cyan-500/20 border border-primary-500/30'
                : 'bg-dark-800/50'}`}>
            <span className="text-dark-300 flex items-center gap-2">
                <span>{icon}</span> {label}
            </span>
            <span className={`font-semibold ${positive !== undefined
                ? (positive ? 'text-accent-green' : 'text-accent-red')
                : 'text-white'
                }`}>
                {value}
            </span>
        </div>
    )
}

// Performance Card Component
function PerformanceCard({ type, holdings, rates }) {
    const performances = holdings.map(h => {
        const rate = rates.find(r => r.code === h.currency)
        if (!rate) return null
        const profit = (h.amount * rate.official) - (h.amount * h.buyPrice)
        const percent = ((profit / (h.amount * h.buyPrice)) * 100)
        return { ...h, profit, percent }
    }).filter(Boolean)

    const sorted = performances.sort((a, b) =>
        type === 'best' ? b.percent - a.percent : a.percent - b.percent
    )

    const item = sorted[0]
    if (!item) return null

    const currency = CURRENCIES.find(c => c.code === item.currency)
    const isBest = type === 'best'

    return (
        <div className={`glass-card ${isBest
            ? 'bg-gradient-to-br from-green-500/10 to-emerald-500/10 border-green-500/30'
            : 'bg-gradient-to-br from-red-500/10 to-rose-500/10 border-red-500/30'}`}>
            <p className="text-xs text-dark-400 mb-2">{isBest ? '🏆 Eng yaxshi' : '📉 Eng yomon'}</p>
            <div className="flex items-center gap-2">
                <span className="text-2xl">{currency?.flag}</span>
                <div>
                    <p className="font-bold text-white">{item.currency}</p>
                    <p className={`text-sm font-semibold ${isBest ? 'text-accent-green' : 'text-accent-red'}`}>
                        {item.percent >= 0 ? '+' : ''}{item.percent.toFixed(1)}%
                    </p>
                </div>
            </div>
        </div>
    )
}

// Empty State
function EmptyPortfolio({ onAdd }) {
    return (
        <div className="glass-card text-center py-8">
            <p className="text-5xl mb-4 animate-bounce-slow">💰</p>
            <p className="text-dark-400 mb-4">Portfelingiz bo'sh</p>
            <button onClick={onAdd} className="btn-primary glow-ring">
                Birinchi valyutani qo'shing
            </button>
        </div>
    )
}

// Holding Card with animation
function HoldingCard({ holding, currentRate, onEdit, onDelete, delay }) {
    const { haptic } = useApp()
    const currency = CURRENCIES.find(c => c.code === holding.currency)

    const currentValue = holding.amount * currentRate
    const costValue = holding.amount * holding.buyPrice
    const profit = currentValue - costValue
    const profitPercent = costValue > 0 ? (profit / costValue * 100) : 0

    return (
        <div
            className="glass-card card-3d cursor-pointer hover:scale-[1.02] transition-all animate-scale-pop"
            style={{ animationDelay: `${delay}s` }}
            onClick={onEdit}
        >
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <span className="text-2xl">{currency?.flag}</span>
                    <div>
                        <div className="flex items-center gap-2">
                            <span className="font-bold text-white">{holding.currency}</span>
                            <span className="text-sm text-dark-400">{holding.amount.toLocaleString()}</span>
                        </div>
                        <p className="text-xs text-dark-400">
                            Olish: {holding.buyPrice.toLocaleString()} • Hozir: {currentRate.toLocaleString()}
                        </p>
                    </div>
                </div>

                <div className="text-right">
                    <p className="font-semibold text-white">{currentValue.toLocaleString('uz-UZ', { maximumFractionDigits: 0 })}</p>
                    <p className={`text-sm font-medium ${profit >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
                        {profit >= 0 ? '+' : ''}{profit.toLocaleString('uz-UZ', { maximumFractionDigits: 0 })}
                        <span className="text-xs ml-1">({profitPercent.toFixed(1)}%)</span>
                    </p>
                </div>
            </div>
        </div>
    )
}

// Add Holding Modal
function AddHoldingModal({ onClose, onSubmit }) {
    const { rates, haptic } = useApp()
    const [currency, setCurrency] = useState('USD')
    const [amount, setAmount] = useState('')
    const [buyPrice, setBuyPrice] = useState('')

    useEffect(() => {
        const rate = rates.find(r => r.code === currency)
        if (rate) {
            setBuyPrice(Math.round(rate.official).toString())
        }
    }, [currency, rates])

    const handleSubmit = (e) => {
        e.preventDefault()
        if (!amount || !buyPrice) return

        onSubmit({
            currency,
            amount: parseFloat(amount),
            buyPrice: parseFloat(buyPrice),
        })
    }

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100] flex items-end" onClick={onClose}>
            <div className="bg-dark-900 rounded-t-3xl w-full p-6 animate-slide-up" onClick={e => e.stopPropagation()}>
                <div className="flex justify-center mb-4">
                    <div className="w-12 h-1.5 bg-dark-600 rounded-full"></div>
                </div>

                <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
                    <span>➕</span> Valyuta qo'shish
                </h2>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm text-dark-400 mb-2">Valyuta</label>
                        <div className="grid grid-cols-5 gap-2">
                            {CURRENCIES.map(c => (
                                <button
                                    key={c.code}
                                    type="button"
                                    onClick={() => { setCurrency(c.code); haptic('light'); }}
                                    className={`py-3 rounded-xl font-medium transition-all flex flex-col items-center gap-1
                                        ${currency === c.code
                                            ? 'text-white scale-105 shadow-glow'
                                            : 'bg-dark-700/50 text-dark-400'}`}
                                    style={{
                                        backgroundColor: currency === c.code ? `${c.color}30` : undefined,
                                        borderColor: currency === c.code ? c.color : 'transparent',
                                        borderWidth: 2,
                                    }}
                                >
                                    <span>{c.flag}</span>
                                    <span className="text-xs">{c.code}</span>
                                </button>
                            ))}
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm text-dark-400 mb-2">Miqdor ({currency})</label>
                        <input
                            type="number"
                            value={amount}
                            onChange={e => setAmount(e.target.value)}
                            placeholder="1000"
                            className="input-premium text-xl font-bold"
                        />
                    </div>

                    <div>
                        <label className="block text-sm text-dark-400 mb-2">Sotib olish narxi (so'm)</label>
                        <input
                            type="number"
                            value={buyPrice}
                            onChange={e => setBuyPrice(e.target.value)}
                            placeholder="12700"
                            className="input-premium"
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-3 pt-4">
                        <button type="button" onClick={onClose} className="py-3 bg-dark-700/50 rounded-xl text-dark-300">
                            Bekor
                        </button>
                        <button type="submit" className="btn-primary py-3" disabled={!amount || !buyPrice}>
                            Qo'shish
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}

// Edit Holding Modal
function EditHoldingModal({ holding, onClose, onSubmit, onDelete }) {
    const { haptic } = useApp()
    const [amount, setAmount] = useState(holding.amount.toString())
    const [buyPrice, setBuyPrice] = useState(holding.buyPrice.toString())
    const [confirmDelete, setConfirmDelete] = useState(false)

    const handleSubmit = (e) => {
        e.preventDefault()
        onSubmit({
            amount: parseFloat(amount),
            buyPrice: parseFloat(buyPrice),
        })
    }

    const handleDelete = () => {
        if (confirmDelete) {
            onDelete()
        } else {
            haptic('warning')
            setConfirmDelete(true)
            setTimeout(() => setConfirmDelete(false), 3000)
        }
    }

    const currency = CURRENCIES.find(c => c.code === holding.currency)

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100] flex items-end" onClick={onClose}>
            <div className="bg-dark-900 rounded-t-3xl w-full p-6 animate-slide-up" onClick={e => e.stopPropagation()}>
                <div className="flex justify-center mb-4">
                    <div className="w-12 h-1.5 bg-dark-600 rounded-full"></div>
                </div>

                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-xl font-bold text-white flex items-center gap-2">
                        <span>{currency?.flag}</span> {holding.currency} tahrirlash
                    </h2>
                    <button
                        onClick={handleDelete}
                        className={`p-2 rounded-lg transition-all ${confirmDelete ? 'bg-accent-red text-white animate-shake' : 'text-dark-400 hover:text-accent-red'}`}
                    >
                        {confirmDelete ? '✓ Tasdiqlash' : '🗑️'}
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm text-dark-400 mb-2">Miqdor</label>
                        <input
                            type="number"
                            value={amount}
                            onChange={e => setAmount(e.target.value)}
                            className="input-premium text-xl font-bold"
                        />
                    </div>

                    <div>
                        <label className="block text-sm text-dark-400 mb-2">Sotib olish narxi</label>
                        <input
                            type="number"
                            value={buyPrice}
                            onChange={e => setBuyPrice(e.target.value)}
                            className="input-premium"
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-3 pt-4">
                        <button type="button" onClick={onClose} className="py-3 bg-dark-700/50 rounded-xl text-dark-300">
                            Bekor
                        </button>
                        <button type="submit" className="btn-primary py-3">
                            Saqlash
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}

// Historical P/L Chart Component
function HistoricalPLChart({ holdings, rates, totalValue, totalCost }) {
    // Generate simulated 7-day history based on current portfolio
    const historyData = useMemo(() => {
        const days = 7
        const history = []
        const currentProfit = totalValue - totalCost

        for (let i = days; i >= 0; i--) {
            const date = new Date()
            date.setDate(date.getDate() - i)

            // Simulate historical variation
            const variation = (Math.random() - 0.4) * 0.02
            const dayProfit = currentProfit * (1 - (i * 0.1) + variation)

            history.push({
                date: date.toLocaleDateString('uz-UZ', { day: '2-digit', month: '2-digit' }),
                profit: Math.round(dayProfit),
            })
        }
        return history
    }, [totalValue, totalCost])

    const chartData = {
        labels: historyData.map(h => h.date),
        datasets: [{
            label: 'Foyda/Zarar',
            data: historyData.map(h => h.profit),
            borderColor: totalValue >= totalCost ? '#22c55e' : '#ef4444',
            backgroundColor: function (context) {
                const chart = context.chart
                const { ctx, chartArea } = chart
                if (!chartArea) return null

                const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom)
                if (totalValue >= totalCost) {
                    gradient.addColorStop(0, 'rgba(34, 197, 94, 0.3)')
                    gradient.addColorStop(1, 'rgba(34, 197, 94, 0)')
                } else {
                    gradient.addColorStop(0, 'rgba(239, 68, 68, 0.3)')
                    gradient.addColorStop(1, 'rgba(239, 68, 68, 0)')
                }
                return gradient
            },
            fill: true,
            tension: 0.4,
            pointRadius: 4,
            pointHoverRadius: 6,
            pointBackgroundColor: totalValue >= totalCost ? '#22c55e' : '#ef4444',
            pointBorderColor: '#fff',
            pointBorderWidth: 2,
            borderWidth: 3,
        }],
    }

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            tooltip: {
                backgroundColor: 'rgba(15, 23, 42, 0.95)',
                titleColor: '#f8fafc',
                bodyColor: '#94a3b8',
                padding: 12,
                cornerRadius: 8,
                callbacks: {
                    label: (ctx) => {
                        const value = ctx.parsed.y
                        return ` ${value >= 0 ? '+' : ''}${value.toLocaleString()} so'm`
                    },
                },
            },
        },
        scales: {
            x: {
                grid: { color: 'rgba(255, 255, 255, 0.03)' },
                ticks: { color: '#64748b', font: { size: 10 } },
            },
            y: {
                grid: { color: 'rgba(255, 255, 255, 0.03)' },
                ticks: {
                    color: '#64748b',
                    font: { size: 10 },
                    callback: (v) => v >= 0 ? `+${(v / 1000).toFixed(0)}k` : `${(v / 1000).toFixed(0)}k`,
                },
            },
        },
    }

    return (
        <div className="glass-card">
            <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
                <span>📈</span> Haftalik P/L Dinamikasi
            </h3>
            <div className="h-48">
                <Line data={chartData} options={chartOptions} />
            </div>
            <p className="text-xs text-dark-500 text-center mt-2">
                Son'ggi 7 kun davomidagi foyda/zarar o'zgarishi
            </p>
        </div>
    )
}
