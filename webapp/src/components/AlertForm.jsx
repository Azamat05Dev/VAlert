/**
 * AlertForm - Enhanced Alert Creation Modal with Bank Selection
 * Features: bank selection, currency selection, direction, threshold input, validation
 */
import { useState, useMemo } from 'react'
import { useApp } from '../App'

const CURRENCIES = [
    { code: 'USD', flag: '🇺🇸', name: 'Dollar' },
    { code: 'EUR', flag: '🇪🇺', name: 'Yevro' },
    { code: 'RUB', flag: '🇷🇺', name: 'Rubl' },
    { code: 'GBP', flag: '🇬🇧', name: 'Funt' },
    { code: 'CNY', flag: '🇨🇳', name: 'Yuan' },
]

const BANKS = [
    { code: 'cbu', name: 'Markaziy Bank', emoji: '🏛️', type: 'official' },
    { code: 'nbu', name: 'Milliy Bank', emoji: '🏦', type: 'commercial' },
    { code: 'kapitalbank', name: 'Kapitalbank', emoji: '🏦', type: 'commercial' },
    { code: 'uzumbank', name: 'Uzum Bank', emoji: '🏦', type: 'commercial' },
    { code: 'ipotekabank', name: 'Ipoteka Bank', emoji: '🏦', type: 'commercial' },
    { code: 'xalqbank', name: 'Xalq Banki', emoji: '🏦', type: 'commercial' },
]

// CBU rates (mock)
const CBU_RATES = { USD: 12720, EUR: 13870, RUB: 128, GBP: 16180, CNY: 1752 }

// Spreads for banks
const SPREADS = {
    cbu: { buy: 0, sell: 0 },
    nbu: { buy: -0.5, sell: 0.8 },
    kapitalbank: { buy: -0.4, sell: 0.7 },
    uzumbank: { buy: -0.3, sell: 0.6 },
    ipotekabank: { buy: -0.5, sell: 0.8 },
    xalqbank: { buy: -0.7, sell: 1.0 },
}

const DIRECTIONS = [
    { id: 'above', label: 'Oshganda', icon: '📈', description: 'Kurs oshganda' },
    { id: 'below', label: 'Tushganda', icon: '📉', description: 'Kurs tushganda' },
]

export default function AlertForm({ onClose, onSubmit }) {
    const { haptic } = useApp()
    const [bank, setBank] = useState('cbu')
    const [currency, setCurrency] = useState('USD')
    const [direction, setDirection] = useState('above')
    const [threshold, setThreshold] = useState('')
    const [errors, setErrors] = useState({})
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [showBankList, setShowBankList] = useState(false)

    // Calculate current rate for selected bank and currency
    const currentRate = useMemo(() => {
        const baseRate = CBU_RATES[currency] || 0
        const spread = SPREADS[bank] || { buy: 0, sell: 0 }

        if (bank === 'cbu') {
            return { official: baseRate }
        }

        return {
            buy: Math.round(baseRate * (1 + spread.buy / 100)),
            sell: Math.round(baseRate * (1 + spread.sell / 100)),
        }
    }, [bank, currency])

    const displayRate = currentRate.official || currentRate.buy || 0
    const selectedBank = BANKS.find(b => b.code === bank)

    // Validate form
    const validate = () => {
        const newErrors = {}
        if (!threshold) {
            newErrors.threshold = 'Qiymat kiritish shart'
        } else if (isNaN(threshold) || parseFloat(threshold) <= 0) {
            newErrors.threshold = 'To\'g\'ri qiymat kiriting'
        }
        setErrors(newErrors)
        return Object.keys(newErrors).length === 0
    }

    // Handle submit
    const handleSubmit = async (e) => {
        e.preventDefault()
        if (!validate()) {
            haptic('error')
            return
        }
        setIsSubmitting(true)
        haptic('medium')
        await onSubmit({
            bank,
            currency,
            direction,
            threshold: parseFloat(threshold),
        })
        setIsSubmitting(false)
        onClose()
    }

    const handleBackdropClick = (e) => {
        if (e.target === e.currentTarget) {
            haptic('light')
            onClose()
        }
    }

    const suggestThreshold = () => {
        const suggested = direction === 'above'
            ? Math.round(displayRate * 1.02)
            : Math.round(displayRate * 0.98)
        setThreshold(suggested.toString())
        haptic('light')
    }

    return (
        <div
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100] flex items-end justify-center animate-fade-in"
            onClick={handleBackdropClick}
        >
            <div className="bg-dark-900 rounded-t-3xl w-full max-w-lg animate-slide-up safe-area-bottom max-h-[90vh] overflow-y-auto">
                {/* Handle Bar */}
                <div className="flex justify-center pt-3 pb-2">
                    <div className="w-12 h-1.5 bg-dark-600 rounded-full"></div>
                </div>

                {/* Header */}
                <div className="px-6 pb-4 border-b border-dark-700">
                    <div className="flex items-center justify-between">
                        <h2 className="text-xl font-bold text-white flex items-center gap-2">
                            <span>🔔</span> Yangi Alert
                        </h2>
                        <button
                            onClick={onClose}
                            className="w-8 h-8 rounded-full bg-dark-700 flex items-center justify-center text-dark-400 hover:text-white transition-colors"
                        >
                            ✕
                        </button>
                    </div>
                </div>

                {/* Form */}
                <form onSubmit={handleSubmit} className="p-6 space-y-5">
                    {/* Bank Selection */}
                    <div>
                        <label className="block text-sm text-dark-400 mb-2">🏦 Bank tanlang</label>
                        <button
                            type="button"
                            onClick={() => { setShowBankList(!showBankList); haptic('light'); }}
                            className="w-full p-3 bg-dark-800/50 rounded-xl flex items-center justify-between border border-dark-600"
                        >
                            <div className="flex items-center gap-2">
                                <span className="text-xl">{selectedBank?.emoji}</span>
                                <span className="font-medium text-white">{selectedBank?.name}</span>
                            </div>
                            <span className="text-dark-400">{showBankList ? '▲' : '▼'}</span>
                        </button>

                        {/* Bank List Dropdown */}
                        {showBankList && (
                            <div className="mt-2 bg-dark-800 rounded-xl border border-dark-600 overflow-hidden">
                                {BANKS.map(b => (
                                    <button
                                        key={b.code}
                                        type="button"
                                        onClick={() => { setBank(b.code); setShowBankList(false); haptic('light'); }}
                                        className={`w-full p-3 flex items-center gap-3 text-left transition-colors
                      ${bank === b.code ? 'bg-primary-500/20 text-white' : 'hover:bg-dark-700/50 text-dark-300'}`}
                                    >
                                        <span className="text-lg">{b.emoji}</span>
                                        <div>
                                            <p className="font-medium">{b.name}</p>
                                            <p className="text-xs text-dark-400">
                                                {b.type === 'official' ? 'Rasmiy kurs' : 'Tijorat banki'}
                                            </p>
                                        </div>
                                        {bank === b.code && <span className="ml-auto text-primary-400">✓</span>}
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Currency Selection */}
                    <div>
                        <label className="block text-sm text-dark-400 mb-2">💱 Valyuta</label>
                        <div className="grid grid-cols-5 gap-2">
                            {CURRENCIES.map(c => (
                                <button
                                    key={c.code}
                                    type="button"
                                    onClick={() => { setCurrency(c.code); haptic('light'); }}
                                    className={`py-3 rounded-xl font-medium transition-all flex flex-col items-center gap-1
                    ${currency === c.code
                                            ? 'bg-primary-500 text-white scale-105 shadow-glow'
                                            : 'bg-dark-700/50 text-dark-400 hover:text-white'}`}
                                >
                                    <span className="text-xl">{c.flag}</span>
                                    <span className="text-xs">{c.code}</span>
                                </button>
                            ))}
                        </div>

                        {/* Current Rate Display */}
                        <div className="mt-3 p-3 bg-dark-800/50 rounded-xl">
                            <div className="flex items-center justify-between mb-1">
                                <span className="text-dark-400 text-sm">{selectedBank?.name} kursi:</span>
                            </div>
                            {bank === 'cbu' ? (
                                <p className="font-bold text-white text-lg">{currentRate.official?.toLocaleString()} so'm</p>
                            ) : (
                                <div className="flex items-center gap-4">
                                    <div>
                                        <p className="text-xs text-dark-400">Olish</p>
                                        <p className="font-bold text-accent-green">{currentRate.buy?.toLocaleString()}</p>
                                    </div>
                                    <div className="w-px h-6 bg-dark-600"></div>
                                    <div>
                                        <p className="text-xs text-dark-400">Sotish</p>
                                        <p className="font-bold text-accent-red">{currentRate.sell?.toLocaleString()}</p>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Direction Selection */}
                    <div>
                        <label className="block text-sm text-dark-400 mb-2">📊 Shart</label>
                        <div className="grid grid-cols-2 gap-3">
                            {DIRECTIONS.map(d => (
                                <button
                                    key={d.id}
                                    type="button"
                                    onClick={() => { setDirection(d.id); haptic('light'); }}
                                    className={`p-3 rounded-xl transition-all text-center
                    ${direction === d.id
                                            ? (d.id === 'above'
                                                ? 'bg-accent-green/20 border-2 border-accent-green'
                                                : 'bg-accent-red/20 border-2 border-accent-red')
                                            : 'bg-dark-700/50 border-2 border-transparent'}`}
                                >
                                    <span className="text-xl">{d.icon}</span>
                                    <p className={`font-medium ${direction === d.id ? 'text-white' : 'text-dark-300'}`}>
                                        {d.label}
                                    </p>
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Threshold Input */}
                    <div>
                        <div className="flex items-center justify-between mb-2">
                            <label className="text-sm text-dark-400">Chegara qiymati</label>
                            <button
                                type="button"
                                onClick={suggestThreshold}
                                className="text-xs text-primary-400 hover:text-primary-300 transition-colors"
                            >
                                💡 Tavsiya
                            </button>
                        </div>
                        <div className="relative">
                            <input
                                type="number"
                                value={threshold}
                                onChange={(e) => setThreshold(e.target.value)}
                                placeholder={`Masalan: ${Math.round(displayRate * (direction === 'above' ? 1.02 : 0.98))}`}
                                className={`input-premium text-xl font-bold pr-16 ${errors.threshold ? 'border-accent-red' : ''}`}
                            />
                            <span className="absolute right-4 top-1/2 -translate-y-1/2 text-dark-400">so'm</span>
                        </div>
                        {errors.threshold && (
                            <p className="text-accent-red text-sm mt-2 flex items-center gap-1">
                                <span>⚠️</span> {errors.threshold}
                            </p>
                        )}
                    </div>

                    {/* Preview */}
                    <div className="p-4 bg-gradient-to-r from-primary-500/20 to-primary-600/20 rounded-xl border border-primary-500/30">
                        <p className="text-sm text-dark-300 mb-2">Alert xulosasi:</p>
                        <p className="font-semibold text-white text-sm">
                            {selectedBank?.emoji} <span className="text-primary-400">{selectedBank?.name}</span>da{' '}
                            {direction === 'above' ? '📈' : '📉'} {currency}{' '}
                            <span className={direction === 'above' ? 'text-accent-green' : 'text-accent-red'}>
                                {threshold ? parseFloat(threshold).toLocaleString() : '...'} so'm
                            </span>
                            {direction === 'above' ? ' dan oshganda' : ' dan tushganda'} xabar berish
                        </p>
                    </div>

                    {/* Submit Buttons */}
                    <div className="grid grid-cols-2 gap-3 pt-2">
                        <button
                            type="button"
                            onClick={onClose}
                            className="py-4 rounded-xl bg-dark-700/50 text-dark-300 font-medium hover:text-white transition-colors"
                        >
                            Bekor qilish
                        </button>
                        <button
                            type="submit"
                            disabled={isSubmitting}
                            className="btn-primary py-4 flex items-center justify-center gap-2"
                        >
                            {isSubmitting ? (
                                <span className="animate-spin">⏳</span>
                            ) : (
                                <>
                                    <span>✓</span> Yaratish
                                </>
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}
