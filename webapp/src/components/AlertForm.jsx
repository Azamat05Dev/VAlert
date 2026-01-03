/**
 * AlertForm - Create new price alerts
 */
import { useState } from 'react';

const CURRENCIES = [
    { code: 'USD', name: 'AQSh Dollari', icon: '💵' },
    { code: 'EUR', name: 'Yevro', icon: '💶' },
    { code: 'RUB', name: 'Rossiya Rubli', icon: '🪙' },
    { code: 'GBP', name: 'Funt Sterling', icon: '💷' },
];

const CURRENT_RATES = { USD: 12720, EUR: 13870, RUB: 128, GBP: 16180 };

export default function AlertForm({ onClose, onSubmit }) {
    const [currency, setCurrency] = useState('USD');
    const [direction, setDirection] = useState('above');
    const [threshold, setThreshold] = useState('');
    const [loading, setLoading] = useState(false);

    const currentRate = CURRENT_RATES[currency] || 0;

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!threshold) return;

        setLoading(true);

        // Haptic feedback
        window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium');

        try {
            await onSubmit?.({ currency, direction, threshold: parseFloat(threshold) });
            onClose?.();
        } catch (error) {
            console.error('Failed to create alert:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-end justify-center z-50 animate-fade-in">
            <div className="w-full max-w-lg bg-dark-800 rounded-t-3xl p-6 animate-slide-up">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-xl font-bold text-white">🔔 Yangi Alert</h2>
                    <button
                        onClick={onClose}
                        className="w-10 h-10 rounded-full bg-dark-700 flex items-center justify-center text-dark-400 hover:text-white transition-colors"
                    >
                        ✕
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="space-y-5">
                    {/* Currency Selection */}
                    <div>
                        <label className="block text-sm text-dark-400 mb-2">Valyuta</label>
                        <div className="grid grid-cols-4 gap-2">
                            {CURRENCIES.map(c => (
                                <button
                                    key={c.code}
                                    type="button"
                                    onClick={() => setCurrency(c.code)}
                                    className={`p-3 rounded-xl text-center transition-all
                    ${currency === c.code
                                            ? 'bg-primary-500/20 border-2 border-primary-500 text-white'
                                            : 'bg-dark-700/50 border-2 border-transparent text-dark-400 hover:text-white'}`}
                                >
                                    <span className="text-2xl">{c.icon}</span>
                                    <p className="text-xs mt-1 font-medium">{c.code}</p>
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Direction */}
                    <div>
                        <label className="block text-sm text-dark-400 mb-2">Shart</label>
                        <div className="grid grid-cols-2 gap-3">
                            <button
                                type="button"
                                onClick={() => setDirection('above')}
                                className={`p-4 rounded-xl flex items-center gap-3 transition-all
                  ${direction === 'above'
                                        ? 'bg-accent-green/20 border-2 border-accent-green text-accent-green'
                                        : 'bg-dark-700/50 border-2 border-transparent text-dark-400 hover:text-white'}`}
                            >
                                <span className="text-2xl">📈</span>
                                <div className="text-left">
                                    <p className="font-semibold">Yuqori</p>
                                    <p className="text-xs opacity-70">Kurs oshganda</p>
                                </div>
                            </button>
                            <button
                                type="button"
                                onClick={() => setDirection('below')}
                                className={`p-4 rounded-xl flex items-center gap-3 transition-all
                  ${direction === 'below'
                                        ? 'bg-accent-red/20 border-2 border-accent-red text-accent-red'
                                        : 'bg-dark-700/50 border-2 border-transparent text-dark-400 hover:text-white'}`}
                            >
                                <span className="text-2xl">📉</span>
                                <div className="text-left">
                                    <p className="font-semibold">Past</p>
                                    <p className="text-xs opacity-70">Kurs tushganda</p>
                                </div>
                            </button>
                        </div>
                    </div>

                    {/* Threshold */}
                    <div>
                        <label className="block text-sm text-dark-400 mb-2">
                            Chegara qiymati (hozir: {currentRate.toLocaleString()})
                        </label>
                        <input
                            type="number"
                            value={threshold}
                            onChange={(e) => setThreshold(e.target.value)}
                            placeholder={String(direction === 'above' ? currentRate + 100 : currentRate - 100)}
                            className="input-premium text-lg"
                            required
                        />
                    </div>

                    {/* Preview */}
                    <div className="p-4 bg-dark-700/50 rounded-xl">
                        <p className="text-sm text-dark-400">Alert aktivlashadi qachonki:</p>
                        <p className="text-white font-semibold mt-1">
                            {currency} kursi {direction === 'above' ? '📈 yuqori' : '📉 past'} bo'lsa:{' '}
                            <span className={direction === 'above' ? 'text-accent-green' : 'text-accent-red'}>
                                {threshold || '...'} so'm
                            </span>
                        </p>
                    </div>

                    {/* Submit */}
                    <button
                        type="submit"
                        disabled={loading || !threshold}
                        className={`w-full py-4 rounded-xl font-semibold text-white transition-all
              ${loading || !threshold
                                ? 'bg-dark-600 cursor-not-allowed'
                                : 'btn-primary'}`}
                    >
                        {loading ? (
                            <span className="flex items-center justify-center gap-2">
                                <span className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                                Yaratilmoqda...
                            </span>
                        ) : (
                            '✅ Alert yaratish'
                        )}
                    </button>
                </form>
            </div>
        </div>
    );
}
