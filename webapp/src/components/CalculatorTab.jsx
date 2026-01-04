/**
 * CalculatorTab - Currency Calculator with Bank Selection
 * Convert currencies using bank-specific buy/sell rates
 */
import { useState, useMemo } from 'react'
import { useApp } from '../App'

const CURRENCIES = [
    { code: 'USD', flag: '🇺🇸', name: 'Dollar' },
    { code: 'EUR', flag: '🇪🇺', name: 'Yevro' },
    { code: 'RUB', flag: '🇷🇺', name: 'Rubl' },
    { code: 'GBP', flag: '🇬🇧', name: 'Funt' },
]

const BANKS = [
    { code: 'cbu', name: 'Markaziy Bank', emoji: '🏛️', type: 'official' },
    { code: 'nbu', name: 'Milliy Bank', emoji: '🏦', type: 'commercial' },
    { code: 'kapitalbank', name: 'Kapitalbank', emoji: '🏦', type: 'commercial' },
    { code: 'uzumbank', name: 'Uzum Bank', emoji: '🏦', type: 'commercial' },
    { code: 'xalqbank', name: 'Xalq Banki', emoji: '🏦', type: 'commercial' },
    { code: 'ipotekabank', name: 'Ipoteka Bank', emoji: '🏦', type: 'commercial' },
]

// Base rates
const CBU_RATES = { USD: 12720, EUR: 13870, RUB: 128, GBP: 16180 }

// Spreads
const SPREADS = {
    cbu: { buy: 0, sell: 0 },
    nbu: { buy: -0.5, sell: 0.8 },
    kapitalbank: { buy: -0.4, sell: 0.7 },
    uzumbank: { buy: -0.3, sell: 0.6 },
    xalqbank: { buy: -0.7, sell: 1.0 },
    ipotekabank: { buy: -0.5, sell: 0.8 },
}

export default function CalculatorTab() {
    const { calcHistory, addToCalcHistory, haptic, showToast } = useApp()
    const [bank, setBank] = useState('cbu')
    const [amount, setAmount] = useState('')
    const [currency, setCurrency] = useState('USD')
    const [direction, setDirection] = useState('buy') // buy = valyuta sotib olish, sell = valyuta sotish
    const [copied, setCopied] = useState(false)
    const [showBankList, setShowBankList] = useState(false)

    // Calculate rates for selected bank
    const bankRates = useMemo(() => {
        const baseRate = CBU_RATES[currency] || 0
        const spread = SPREADS[bank] || { buy: 0, sell: 0 }

        if (bank === 'cbu') {
            return { buy: baseRate, sell: baseRate, official: baseRate }
        }

        return {
            buy: Math.round(baseRate * (1 + spread.buy / 100)),
            sell: Math.round(baseRate * (1 + spread.sell / 100)),
        }
    }, [bank, currency])

    // Get active rate based on direction
    const activeRate = direction === 'buy' ? bankRates.sell : bankRates.buy
    const result = amount ? parseFloat(amount) * activeRate : 0
    const selectedBank = BANKS.find(b => b.code === bank)

    // Copy result
    const handleCopy = () => {
        haptic('light')
        navigator.clipboard.writeText(Math.round(result).toLocaleString())
        setCopied(true)
        showToast('Nusxalandi ✓', 'success')
        setTimeout(() => setCopied(false), 2000)
    }

    // Save to history
    const handleSave = () => {
        if (!amount) return
        haptic('medium')
        addToCalcHistory({
            bank,
            bankName: selectedBank?.name,
            amount: parseFloat(amount),
            currency,
            direction,
            rate: activeRate,
            result: Math.round(result),
            timestamp: new Date().toISOString(),
        })
        showToast('Tarixga saqlandi ✓', 'success')
    }

    return (
        <div className="space-y-4 animate-fade-in">
            <div className="glass-card">
                <h2 className="text-xl font-bold text-white mb-5 flex items-center gap-2">
                    <span>🧮</span> Valyuta Kalkulyatori
                </h2>

                <div className="space-y-4">
                    {/* Bank Selection */}
                    <div>
                        <label className="block text-sm text-dark-400 mb-2">🏦 Bank</label>
                        <button
                            onClick={() => { setShowBankList(!showBankList); haptic('light'); }}
                            className="w-full p-3 bg-dark-800/50 rounded-xl flex items-center justify-between border border-dark-600"
                        >
                            <div className="flex items-center gap-2">
                                <span className="text-lg">{selectedBank?.emoji}</span>
                                <span className="font-medium text-white">{selectedBank?.name}</span>
                            </div>
                            <span className="text-dark-400">{showBankList ? '▲' : '▼'}</span>
                        </button>

                        {showBankList && (
                            <div className="mt-2 bg-dark-800 rounded-xl border border-dark-600 overflow-hidden max-h-48 overflow-y-auto">
                                {BANKS.map(b => (
                                    <button
                                        key={b.code}
                                        onClick={() => { setBank(b.code); setShowBankList(false); haptic('light'); }}
                                        className={`w-full p-3 flex items-center gap-3 text-left transition-colors
                      ${bank === b.code ? 'bg-primary-500/20 text-white' : 'hover:bg-dark-700/50 text-dark-300'}`}
                                    >
                                        <span>{b.emoji}</span>
                                        <span className="font-medium">{b.name}</span>
                                        {bank === b.code && <span className="ml-auto text-primary-400">✓</span>}
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Amount Input */}
                    <div>
                        <label className="block text-sm text-dark-400 mb-2">Miqdor</label>
                        <div className="relative">
                            <input
                                type="number"
                                value={amount}
                                onChange={(e) => setAmount(e.target.value)}
                                placeholder="100"
                                className="input-premium text-2xl font-bold pr-16"
                            />
                            <span className="absolute right-4 top-1/2 -translate-y-1/2 text-dark-400 font-bold">
                                {currency}
                            </span>
                        </div>
                    </div>

                    {/* Currency Selector */}
                    <div>
                        <label className="block text-sm text-dark-400 mb-2">Valyuta</label>
                        <div className="grid grid-cols-4 gap-2">
                            {CURRENCIES.map(c => (
                                <button
                                    key={c.code}
                                    onClick={() => { setCurrency(c.code); haptic('light'); }}
                                    className={`py-3 rounded-xl font-semibold transition-all flex flex-col items-center gap-1
                    ${currency === c.code
                                            ? 'bg-primary-500 text-white shadow-glow scale-105'
                                            : 'bg-dark-700/50 text-dark-400 hover:text-white'}`}
                                >
                                    <span>{c.flag}</span>
                                    <span className="text-sm">{c.code}</span>
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Direction - Buy/Sell */}
                    <div>
                        <label className="block text-sm text-dark-400 mb-2">Amal</label>
                        <div className="grid grid-cols-2 gap-3">
                            <button
                                onClick={() => { setDirection('buy'); haptic('light'); }}
                                className={`py-3 rounded-xl font-medium transition-all flex items-center justify-center gap-2
                  ${direction === 'buy'
                                        ? 'bg-accent-green/20 text-accent-green border-2 border-accent-green'
                                        : 'bg-dark-700/50 text-dark-400 border-2 border-transparent'}`}
                            >
                                <span>💵</span> Valyuta olish
                            </button>
                            <button
                                onClick={() => { setDirection('sell'); haptic('light'); }}
                                className={`py-3 rounded-xl font-medium transition-all flex items-center justify-center gap-2
                  ${direction === 'sell'
                                        ? 'bg-accent-red/20 text-accent-red border-2 border-accent-red'
                                        : 'bg-dark-700/50 text-dark-400 border-2 border-transparent'}`}
                            >
                                <span>💰</span> Valyuta sotish
                            </button>
                        </div>
                    </div>

                    {/* Bank Rates Info */}
                    <div className="p-3 bg-dark-800/50 rounded-xl">
                        <p className="text-xs text-dark-400 mb-2">{selectedBank?.name} kurslari:</p>
                        <div className="flex items-center gap-4">
                            <div className={`${direction === 'sell' ? 'opacity-100' : 'opacity-50'}`}>
                                <p className="text-xs text-dark-400">Sotib olish</p>
                                <p className="font-bold text-accent-green">{bankRates.buy?.toLocaleString()}</p>
                            </div>
                            <div className="w-px h-8 bg-dark-600"></div>
                            <div className={`${direction === 'buy' ? 'opacity-100' : 'opacity-50'}`}>
                                <p className="text-xs text-dark-400">Sotish</p>
                                <p className="font-bold text-accent-red">{bankRates.sell?.toLocaleString()}</p>
                            </div>
                            <div className="ml-auto text-xs text-dark-400">
                                Ishlatilmoqda: <span className="text-white">{activeRate.toLocaleString()}</span>
                            </div>
                        </div>
                    </div>

                    {/* Result */}
                    <div className="p-5 bg-gradient-to-r from-primary-500/20 to-primary-600/20 rounded-xl border border-primary-500/30">
                        <div className="flex items-start justify-between">
                            <div>
                                <p className="text-sm text-dark-300 mb-1">Natija</p>
                                <p className="text-3xl font-bold text-white">
                                    {result.toLocaleString('uz-UZ', { maximumFractionDigits: 0 })}
                                    <span className="text-lg text-dark-400 ml-2">so'm</span>
                                </p>
                            </div>
                            <button
                                onClick={handleCopy}
                                className="p-3 glass-button rounded-xl active:scale-95 transition-transform"
                            >
                                {copied ? '✅' : '📋'}
                            </button>
                        </div>
                        <p className="text-xs text-dark-400 mt-3">
                            {amount || 0} {currency} × {activeRate.toLocaleString()} = {result.toLocaleString('uz-UZ', { maximumFractionDigits: 0 })} so'm
                        </p>
                    </div>

                    {/* Actions */}
                    <div className="grid grid-cols-2 gap-3">
                        <button
                            onClick={handleSave}
                            className="btn-primary py-3"
                            disabled={!amount}
                        >
                            💾 Saqlash
                        </button>
                        <button
                            onClick={() => setAmount('')}
                            className="py-3 rounded-xl bg-dark-700/50 text-dark-300 font-medium hover:text-white transition-colors"
                        >
                            🗑️ Tozalash
                        </button>
                    </div>
                </div>
            </div>

            {/* Calculation History */}
            {calcHistory.length > 0 && (
                <div className="glass-card">
                    <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
                        <span>📜</span> Tarix
                    </h3>
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                        {calcHistory.slice(0, 5).map((h, i) => (
                            <div key={i} className="p-3 bg-dark-800/50 rounded-lg flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-white">
                                        {h.amount} {h.currency} = <span className="font-bold">{h.result?.toLocaleString()}</span> so'm
                                    </p>
                                    <p className="text-xs text-dark-400">
                                        {h.bankName || 'CBU'} • {h.direction === 'buy' ? 'Olish' : 'Sotish'}
                                    </p>
                                </div>
                                <span className="text-xs text-dark-500">
                                    {new Date(h.timestamp).toLocaleTimeString('uz-UZ', { hour: '2-digit', minute: '2-digit' })}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}
