/**
 * Settings Tab Component
 * Language, theme, notifications, and about
 */
import { useApp } from '../App'

const LANGUAGES = [
    { code: 'uz', name: "O'zbekcha", flag: '🇺🇿' },
    { code: 'ru', name: 'Русский', flag: '🇷🇺' },
    { code: 'en', name: 'English', flag: '🇬🇧' },
]

const THEMES = [
    { id: 'dark', name: 'Qorong\'u', icon: '🌙' },
    { id: 'light', name: 'Yorug\'', icon: '☀️' },
]

export default function SettingsTab() {
    const {
        language,
        setLanguage,
        theme,
        setTheme,
        haptic,
        showToast,
        t
    } = useApp()

    const handleLanguageChange = (code) => {
        haptic('light')
        setLanguage(code)
        showToast(`Til o'zgartirildi: ${LANGUAGES.find(l => l.code === code)?.name}`, 'success')
    }

    const handleThemeChange = (id) => {
        haptic('light')
        setTheme(id)
        showToast(`Tema o'zgartirildi`, 'success')
    }

    return (
        <div className="space-y-6 animate-fade-in">
            {/* Language Selection */}
            <div className="glass-card">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <span>🌐</span> {t('language')}
                </h3>
                <div className="space-y-2">
                    {LANGUAGES.map(lang => (
                        <button
                            key={lang.code}
                            onClick={() => handleLanguageChange(lang.code)}
                            className={`w-full flex items-center gap-4 p-4 rounded-xl transition-all
                ${language === lang.code
                                    ? 'bg-primary-500/20 border-2 border-primary-500'
                                    : 'bg-dark-800/50 border-2 border-transparent hover:border-dark-600'}`}
                        >
                            <span className="text-2xl">{lang.flag}</span>
                            <span className={`font-medium ${language === lang.code ? 'text-white' : 'text-dark-300'}`}>
                                {lang.name}
                            </span>
                            {language === lang.code && (
                                <span className="ml-auto text-primary-400">✓</span>
                            )}
                        </button>
                    ))}
                </div>
            </div>

            {/* Theme Selection */}
            <div className="glass-card">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <span>🎨</span> {t('theme')}
                </h3>
                <div className="grid grid-cols-2 gap-3">
                    {THEMES.map(t => (
                        <button
                            key={t.id}
                            onClick={() => handleThemeChange(t.id)}
                            className={`flex flex-col items-center gap-2 p-4 rounded-xl transition-all
                ${theme === t.id
                                    ? 'bg-primary-500/20 border-2 border-primary-500'
                                    : 'bg-dark-800/50 border-2 border-transparent hover:border-dark-600'}`}
                        >
                            <span className="text-3xl">{t.icon}</span>
                            <span className={`font-medium ${theme === t.id ? 'text-white' : 'text-dark-300'}`}>
                                {t.name}
                            </span>
                        </button>
                    ))}
                </div>
            </div>

            {/* Notification Settings */}
            <div className="glass-card">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <span>🔔</span> Bildirishnomalar
                </h3>
                <div className="space-y-3">
                    <ToggleSetting
                        label="Alert bildirishnomalari"
                        sublabel="Kurs chegara qiymatiga yetganda"
                        defaultChecked={true}
                    />
                    <ToggleSetting
                        label="Kunlik xulosa"
                        sublabel="Har kuni ertalab kurs xulosasi"
                        defaultChecked={false}
                    />
                    <ToggleSetting
                        label="Katta o'zgarishlar"
                        sublabel="Kurs 1%+ o'zgarganda"
                        defaultChecked={true}
                    />
                </div>
            </div>

            {/* Default Currency */}
            <div className="glass-card">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <span>💵</span> Asosiy valyuta
                </h3>
                <div className="grid grid-cols-4 gap-2">
                    {['USD', 'EUR', 'RUB', 'GBP'].map(c => (
                        <button
                            key={c}
                            className="py-3 rounded-xl bg-dark-700/50 text-dark-300 font-medium hover:text-white hover:bg-dark-700 transition-all"
                        >
                            {c}
                        </button>
                    ))}
                </div>
            </div>

            {/* About */}
            <div className="glass-card">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <span>ℹ️</span> {t('about')}
                </h3>
                <div className="space-y-3 text-sm">
                    <div className="flex justify-between">
                        <span className="text-dark-400">Versiya</span>
                        <span className="text-white font-medium">2.0.0</span>
                    </div>
                    <div className="flex justify-between">
                        <span className="text-dark-400">Ishlab chiquvchi</span>
                        <span className="text-white font-medium">@Azamat05Dev</span>
                    </div>
                    <div className="flex justify-between">
                        <span className="text-dark-400">Ma'lumot manbai</span>
                        <span className="text-white font-medium">CBU API</span>
                    </div>
                </div>

                <div className="mt-6 pt-4 border-t border-dark-700">
                    <p className="text-xs text-dark-500 text-center">
                        © 2026 VAlert. Barcha huquqlar himoyalangan.
                    </p>
                </div>
            </div>

            {/* Quick Actions */}
            <div className="grid grid-cols-2 gap-3">
                <button className="glass-button py-4 rounded-xl flex items-center justify-center gap-2 text-dark-300 hover:text-white transition-colors">
                    <span>📤</span> Ulashish
                </button>
                <button className="glass-button py-4 rounded-xl flex items-center justify-center gap-2 text-dark-300 hover:text-white transition-colors">
                    <span>⭐</span> Baholash
                </button>
            </div>
        </div>
    )
}

// Toggle Setting Component
function ToggleSetting({ label, sublabel, defaultChecked }) {
    const [checked, setChecked] = useState(defaultChecked)
    const { haptic } = useApp()

    const toggle = () => {
        haptic('light')
        setChecked(!checked)
    }

    return (
        <button
            onClick={toggle}
            className="w-full flex items-center justify-between p-3 bg-dark-800/50 rounded-xl"
        >
            <div className="text-left">
                <p className="text-white font-medium">{label}</p>
                <p className="text-xs text-dark-400">{sublabel}</p>
            </div>
            <div className={`w-12 h-7 rounded-full transition-all flex items-center px-1
        ${checked ? 'bg-primary-500' : 'bg-dark-600'}`}>
                <div className={`w-5 h-5 rounded-full bg-white transition-transform shadow-md
          ${checked ? 'translate-x-5' : 'translate-x-0'}`}></div>
            </div>
        </button>
    )
}

// Need useState import
import { useState } from 'react'
