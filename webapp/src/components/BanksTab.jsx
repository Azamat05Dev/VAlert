/**
 * BanksTab - Banks List and Rates Comparison
 * Shows all 16 Uzbekistan banks with their exchange rates
 */
import { useState, useEffect, useMemo } from 'react'
import { useApp } from '../App'

// All Uzbekistan Banks (from bot config.py)
const BANKS = {
    cbu: { name: 'Markaziy Bank', type: 'official', emoji: '🏛️' },
    nbu: { name: 'Milliy Bank (NBU)', type: 'commercial', emoji: '🏦' },
    asakabank: { name: 'Asakabank', type: 'commercial', emoji: '🏦' },
    xalqbank: { name: 'Xalq Banki', type: 'commercial', emoji: '🏦' },
    ipotekabank: { name: 'Ipoteka Bank', type: 'commercial', emoji: '🏦' },
    agrobank: { name: 'Agrobank', type: 'commercial', emoji: '🏦' },
    aloqabank: { name: 'Aloqabank', type: 'commercial', emoji: '🏦' },
    kapitalbank: { name: 'Kapitalbank', type: 'commercial', emoji: '🏦' },
    uzumbank: { name: 'Uzum Bank', type: 'commercial', emoji: '🏦' },
    hamkorbank: { name: 'Hamkorbank', type: 'commercial', emoji: '🏦' },
    infinbank: { name: 'Infinbank', type: 'commercial', emoji: '🏦' },
    davr: { name: 'Davr Bank', type: 'commercial', emoji: '🏦' },
    orientfinans: { name: 'Orient Finans', type: 'commercial', emoji: '🏦' },
    anorbank: { name: 'Anorbank', type: 'commercial', emoji: '🏦' },
    tbc: { name: 'TBC Bank', type: 'commercial', emoji: '🏦' },
    ipak: { name: 'Ipak Yo\'li Bank', type: 'commercial', emoji: '🏦' },
    trustbank: { name: 'Trustbank', type: 'commercial', emoji: '🏦' },
}

// Base CBU rates (mock - will be replaced with API)
const CBU_RATES = {
    USD: 12720,
    EUR: 13870,
    RUB: 128.2,
    GBP: 16180,
    CNY: 1752,
    JPY: 83.1,
    KRW: 8.78,
    CHF: 14520,
    TRY: 371,
    KZT: 25.1,
}

// Bank spreads (from config.py)
const SPREADS = {
    nbu: { buy: -0.5, sell: 0.8 },
    asakabank: { buy: -0.6, sell: 0.9 },
    xalqbank: { buy: -0.7, sell: 1.0 },
    ipotekabank: { buy: -0.5, sell: 0.8 },
    agrobank: { buy: -0.6, sell: 0.9 },
    aloqabank: { buy: -0.5, sell: 0.8 },
    kapitalbank: { buy: -0.4, sell: 0.7 },
    uzumbank: { buy: -0.3, sell: 0.6 },
    hamkorbank: { buy: -0.5, sell: 0.8 },
    infinbank: { buy: -0.4, sell: 0.7 },
    davr: { buy: -0.5, sell: 0.8 },
    orientfinans: { buy: -0.4, sell: 0.7 },
    anorbank: { buy: -0.3, sell: 0.6 },
    tbc: { buy: -0.4, sell: 0.7 },
    ipak: { buy: -0.5, sell: 0.8 },
    trustbank: { buy: -0.4, sell: 0.7 },
}

// Calculate bank rates based on CBU + spreads
function getBankRates(bankCode) {
    if (bankCode === 'cbu') {
        return Object.entries(CBU_RATES).map(([code, rate]) => ({
            currency: code,
            official: rate,
        }))
    }

    const spreads = SPREADS[bankCode] || { buy: -0.5, sell: 0.8 }
    return Object.entries(CBU_RATES).map(([code, rate]) => ({
        currency: code,
        buy: Math.round(rate * (1 + spreads.buy / 100)),
        sell: Math.round(rate * (1 + spreads.sell / 100)),
    }))
}

// Views
const VIEWS = {
    LIST: 'list',
    DETAIL: 'detail',
    COMPARE: 'compare',
    BEST: 'best',
}

export default function BanksTab() {
    const { haptic, showToast, t } = useApp()
    const [view, setView] = useState(VIEWS.LIST)
    const [selectedBank, setSelectedBank] = useState(null)
    const [compareCurrency, setCompareCurrency] = useState('USD')
    const [loading, setLoading] = useState(false)

    // Select a bank
    const handleSelectBank = (code) => {
        haptic('light')
        setSelectedBank(code)
        setView(VIEWS.DETAIL)
    }

    // Back to list
    const handleBack = () => {
        haptic('light')
        setView(VIEWS.LIST)
        setSelectedBank(null)
    }

    // Open compare view
    const handleCompare = () => {
        haptic('light')
        setView(VIEWS.COMPARE)
    }

    // Open best rate view
    const handleBest = () => {
        haptic('light')
        setView(VIEWS.BEST)
    }

    // Find best rates across all banks
    const bestRates = useMemo(() => {
        const currencies = ['USD', 'EUR', 'RUB']
        return currencies.map(cur => {
            let bestBuy = { bank: '', rate: 0 }
            let bestSell = { bank: '', rate: Infinity }

            Object.keys(SPREADS).forEach(bankCode => {
                const rates = getBankRates(bankCode)
                const curRate = rates.find(r => r.currency === cur)
                if (curRate) {
                    if (curRate.buy > bestBuy.rate) {
                        bestBuy = { bank: bankCode, rate: curRate.buy }
                    }
                    if (curRate.sell < bestSell.rate) {
                        bestSell = { bank: bankCode, rate: curRate.sell }
                    }
                }
            })

            return { currency: cur, bestBuy, bestSell }
        })
    }, [])

    // Compare rates for selected currency
    const compareRates = useMemo(() => {
        const results = []

        // Add CBU
        const cbuRate = CBU_RATES[compareCurrency]
        results.push({
            bank: 'cbu',
            name: BANKS.cbu.name,
            emoji: BANKS.cbu.emoji,
            official: cbuRate,
        })

        // Add commercial banks
        Object.entries(SPREADS).forEach(([code, spreads]) => {
            const buy = Math.round(cbuRate * (1 + spreads.buy / 100))
            const sell = Math.round(cbuRate * (1 + spreads.sell / 100))
            results.push({
                bank: code,
                name: BANKS[code]?.name || code,
                emoji: '🏦',
                buy,
                sell,
            })
        })

        // Sort by buy rate (highest first - best for selling currency)
        return results.sort((a, b) => (b.buy || b.official) - (a.buy || a.official))
    }, [compareCurrency])

    return (
        <div className="space-y-4 animate-fade-in">
            {/* Bank List View */}
            {view === VIEWS.LIST && (
                <>
                    {/* Quick Actions */}
                    <div className="grid grid-cols-2 gap-3">
                        <button
                            onClick={handleCompare}
                            className="glass-card card-3d py-4 flex items-center justify-center gap-2 hover:scale-105 transition-all duration-300 hover:shadow-glow"
                        >
                            <span className="text-xl">📈</span>
                            <span className="font-medium text-white">Taqqoslash</span>
                        </button>
                        <button
                            onClick={handleBest}
                            className="glass-card card-3d py-4 flex items-center justify-center gap-2 hover:scale-105 transition-all duration-300 bg-gradient-to-r from-amber-500/10 to-yellow-500/10 hover:shadow-glow"
                        >
                            <span className="text-xl">🏆</span>
                            <span className="font-medium text-white">Eng yaxshi</span>
                        </button>
                    </div>

                    {/* Official Bank */}
                    <div className="space-y-3">
                        <h2 className="text-sm font-semibold text-dark-400 uppercase tracking-wide">
                            Rasmiy kurs
                        </h2>
                        <BankCard
                            code="cbu"
                            bank={BANKS.cbu}
                            rates={getBankRates('cbu').slice(0, 3)}
                            onClick={() => handleSelectBank('cbu')}
                        />
                    </div>

                    {/* Commercial Banks */}
                    <div className="space-y-3">
                        <h2 className="text-sm font-semibold text-dark-400 uppercase tracking-wide">
                            Tijorat banklari ({Object.keys(SPREADS).length})
                        </h2>
                        <div className="grid grid-cols-2 gap-3">
                            {Object.entries(BANKS)
                                .filter(([code]) => code !== 'cbu')
                                .map(([code, bank], index) => (
                                    <button
                                        key={code}
                                        onClick={() => handleSelectBank(code)}
                                        className={`glass-card card-3d p-4 text-left hover:scale-[1.02] transition-all animate-scale-pop stagger-${Math.min(index + 1, 6)}`}
                                        style={{ animationDelay: `${index * 0.05}s` }}
                                    >
                                        <div className="flex items-center gap-2 mb-2">
                                            <span className="text-lg">{bank.emoji}</span>
                                            <span className="font-medium text-white text-sm truncate">{bank.name}</span>
                                        </div>
                                        <div className="text-xs text-dark-400">
                                            USD: {getBankRates(code)[0]?.buy?.toLocaleString() || '—'}
                                        </div>
                                    </button>
                                ))}
                        </div>
                    </div>
                </>
            )}

            {/* Bank Detail View */}
            {view === VIEWS.DETAIL && selectedBank && (
                <BankDetailView
                    bankCode={selectedBank}
                    bank={BANKS[selectedBank]}
                    rates={getBankRates(selectedBank)}
                    onBack={handleBack}
                />
            )}

            {/* Compare View */}
            {view === VIEWS.COMPARE && (
                <CompareView
                    currency={compareCurrency}
                    rates={compareRates}
                    onCurrencyChange={setCompareCurrency}
                    onBack={handleBack}
                />
            )}

            {/* Best Rates View */}
            {view === VIEWS.BEST && (
                <BestRatesView
                    bestRates={bestRates}
                    banks={BANKS}
                    onBack={handleBack}
                />
            )}
        </div>
    )
}

// Bank Card Component
function BankCard({ code, bank, rates, onClick }) {
    return (
        <button
            onClick={onClick}
            className="w-full glass-card hover:scale-[1.02] transition-transform text-left"
        >
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                    <span className="text-2xl">{bank.emoji}</span>
                    <div>
                        <h3 className="font-semibold text-white">{bank.name}</h3>
                        <p className="text-xs text-dark-400">
                            {bank.type === 'official' ? 'Rasmiy kurs' : 'Tijorat banki'}
                        </p>
                    </div>
                </div>
                <span className="text-dark-400">→</span>
            </div>

            <div className="grid grid-cols-3 gap-2">
                {rates.slice(0, 3).map(rate => (
                    <div key={rate.currency} className="bg-dark-800/50 rounded-lg p-2 text-center">
                        <p className="text-xs text-dark-400">{rate.currency}</p>
                        <p className="font-semibold text-white text-sm">
                            {(rate.official || rate.buy || 0).toLocaleString()}
                        </p>
                    </div>
                ))}
            </div>
        </button>
    )
}

// Bank Detail View
function BankDetailView({ bankCode, bank, rates, onBack }) {
    const isOfficial = bank.type === 'official'

    return (
        <div className="space-y-4">
            {/* Header */}
            <div className="flex items-center gap-3">
                <button onClick={onBack} className="p-2 glass-button rounded-lg">
                    ←
                </button>
                <div className="flex items-center gap-2">
                    <span className="text-2xl">{bank.emoji}</span>
                    <div>
                        <h2 className="text-lg font-bold text-white">{bank.name}</h2>
                        <p className="text-xs text-dark-400">
                            {isOfficial ? 'Markaziy Bank rasmiy kursi' : 'Tijorat banki kursi'}
                        </p>
                    </div>
                </div>
            </div>

            {/* Legend */}
            {!isOfficial && (
                <div className="flex items-center gap-4 text-sm text-dark-400">
                    <span className="flex items-center gap-1">
                        <span className="text-accent-green">📥</span> Sotib olish
                    </span>
                    <span className="flex items-center gap-1">
                        <span className="text-accent-red">📤</span> Sotish
                    </span>
                </div>
            )}

            {/* Rates List */}
            <div className="space-y-2">
                {rates.map(rate => (
                    <div key={rate.currency} className="glass-card p-3">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <span className="w-10 h-10 rounded-full bg-dark-700 flex items-center justify-center font-bold text-white">
                                    {rate.currency}
                                </span>
                                <span className="text-white font-medium">{rate.currency}/UZS</span>
                            </div>

                            {isOfficial ? (
                                <span className="font-bold text-white text-lg">
                                    {rate.official?.toLocaleString()}
                                </span>
                            ) : (
                                <div className="flex items-center gap-4 text-sm">
                                    <div className="text-right">
                                        <p className="text-xs text-dark-400">Olish</p>
                                        <p className="font-semibold text-accent-green">{rate.buy?.toLocaleString()}</p>
                                    </div>
                                    <div className="w-px h-8 bg-dark-600"></div>
                                    <div className="text-right">
                                        <p className="text-xs text-dark-400">Sotish</p>
                                        <p className="font-semibold text-accent-red">{rate.sell?.toLocaleString()}</p>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>

            {/* Note */}
            {!isOfficial && (
                <p className="text-xs text-dark-500 text-center">
                    ⚠️ Taxminiy kurslar (CBU asosida hisoblangan)
                </p>
            )}
        </div>
    )
}

// Compare View
function CompareView({ currency, rates, onCurrencyChange, onBack }) {
    const currencies = ['USD', 'EUR', 'RUB', 'GBP']

    return (
        <div className="space-y-4">
            {/* Header */}
            <div className="flex items-center gap-3">
                <button onClick={onBack} className="p-2 glass-button rounded-lg">
                    ←
                </button>
                <div>
                    <h2 className="text-lg font-bold text-white">📈 Taqqoslash</h2>
                    <p className="text-xs text-dark-400">Barcha banklar {currency} kursi</p>
                </div>
            </div>

            {/* Currency Selector */}
            <div className="flex gap-2">
                {currencies.map(cur => (
                    <button
                        key={cur}
                        onClick={() => onCurrencyChange(cur)}
                        className={`flex-1 py-2.5 rounded-xl font-medium transition-all
              ${currency === cur
                                ? 'bg-primary-500 text-white shadow-glow'
                                : 'bg-dark-700/50 text-dark-400 hover:text-white'}`}
                    >
                        {cur}
                    </button>
                ))}
            </div>

            {/* Rates List */}
            <div className="space-y-2">
                {rates.map((rate, i) => (
                    <div
                        key={rate.bank}
                        className={`glass-card p-3 flex items-center justify-between
              ${i === 0 ? 'border-2 border-accent-green/50' : ''}`}
                    >
                        <div className="flex items-center gap-3">
                            <span className="text-lg">{rate.emoji}</span>
                            <div>
                                <p className="font-medium text-white text-sm">{rate.name}</p>
                                {i === 0 && <p className="text-xs text-accent-green">🏆 Eng yaxshi</p>}
                            </div>
                        </div>

                        {rate.official ? (
                            <span className="font-bold text-white">{rate.official.toLocaleString()}</span>
                        ) : (
                            <div className="flex items-center gap-3 text-sm">
                                <span className="text-accent-green">{rate.buy?.toLocaleString()}</span>
                                <span className="text-dark-500">/</span>
                                <span className="text-accent-red">{rate.sell?.toLocaleString()}</span>
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    )
}

// Best Rates View
function BestRatesView({ bestRates, banks, onBack }) {
    return (
        <div className="space-y-4">
            {/* Header */}
            <div className="flex items-center gap-3">
                <button onClick={onBack} className="p-2 glass-button rounded-lg">
                    ←
                </button>
                <div>
                    <h2 className="text-lg font-bold text-white">🏆 Eng yaxshi kurslar</h2>
                    <p className="text-xs text-dark-400">Qayerda almashish foydali?</p>
                </div>
            </div>

            {/* Best Rates Cards */}
            <div className="space-y-4">
                {bestRates.map(item => (
                    <div key={item.currency} className="glass-card">
                        <div className="flex items-center gap-2 mb-4">
                            <span className="w-10 h-10 rounded-full bg-primary-500/20 flex items-center justify-center font-bold text-primary-400">
                                {item.currency}
                            </span>
                            <h3 className="font-semibold text-white">{item.currency}/UZS</h3>
                        </div>

                        <div className="grid grid-cols-2 gap-3">
                            {/* Best Buy */}
                            <div className="bg-accent-green/10 border border-accent-green/30 rounded-xl p-3">
                                <p className="text-xs text-dark-400 mb-1">📥 Valyuta sotish</p>
                                <p className="text-lg font-bold text-accent-green">{item.bestBuy.rate.toLocaleString()}</p>
                                <p className="text-xs text-dark-400 mt-1">
                                    {banks[item.bestBuy.bank]?.name || item.bestBuy.bank}
                                </p>
                            </div>

                            {/* Best Sell */}
                            <div className="bg-accent-red/10 border border-accent-red/30 rounded-xl p-3">
                                <p className="text-xs text-dark-400 mb-1">📤 Valyuta olish</p>
                                <p className="text-lg font-bold text-accent-red">{item.bestSell.rate.toLocaleString()}</p>
                                <p className="text-xs text-dark-400 mt-1">
                                    {banks[item.bestSell.bank]?.name || item.bestSell.bank}
                                </p>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Tip */}
            <div className="glass-card bg-primary-500/10 border-primary-500/30">
                <p className="text-sm text-dark-300">
                    💡 <strong>Maslahat:</strong> Valyutani sotish uchun yuqori "Sotib olish" kursini,
                    valyutani olish uchun past "Sotish" kursini tanlang.
                </p>
            </div>
        </div>
    )
}
