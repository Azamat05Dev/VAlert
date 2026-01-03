import { useState, useEffect } from 'react'
import './index.css'

// Telegram WebApp API
const tg = window.Telegram?.WebApp

// Mock data for demo (will be replaced with API)
const MOCK_RATES = [
  { code: 'USD', name: 'AQSh Dollari', buy: 12680, sell: 12750, change: 0.15, official: 12720 },
  { code: 'EUR', name: 'Yevro', buy: 13820, sell: 13920, change: -0.08, official: 13870 },
  { code: 'RUB', name: 'Rossiya Rubli', buy: 127.5, sell: 129.8, change: 0.25, official: 128.2 },
  { code: 'GBP', name: 'Funt Sterling', buy: 16100, sell: 16250, change: 0.12, official: 16180 },
  { code: 'CNY', name: 'Xitoy Yuani', buy: 1745, sell: 1768, change: -0.05, official: 1752 },
]

// Tab definitions
const TABS = [
  { id: 'rates', icon: '📊', label: 'Kurslar' },
  { id: 'calc', icon: '🧮', label: 'Kalkulyator' },
  { id: 'alerts', icon: '🔔', label: 'Alertlar' },
  { id: 'settings', icon: '⚙️', label: 'Sozlamalar' },
]

function App() {
  const [activeTab, setActiveTab] = useState('rates')
  const [rates, setRates] = useState(MOCK_RATES)
  const [loading, setLoading] = useState(false)
  const [lastUpdate, setLastUpdate] = useState(new Date())

  useEffect(() => {
    // Initialize Telegram WebApp
    if (tg) {
      tg.ready()
      tg.expand()
      tg.setHeaderColor('#0f172a')
      tg.setBackgroundColor('#0f172a')
    }
  }, [])

  const refreshRates = async () => {
    setLoading(true)
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000))
    setLastUpdate(new Date())
    setLoading(false)
  }

  return (
    <div className="min-h-screen pb-24 safe-area-top safe-area-bottom">
      {/* Header */}
      <Header lastUpdate={lastUpdate} onRefresh={refreshRates} loading={loading} />

      {/* Main Content */}
      <main className="px-4 py-6 animate-fade-in">
        {activeTab === 'rates' && <RatesTab rates={rates} loading={loading} />}
        {activeTab === 'calc' && <CalculatorTab rates={rates} />}
        {activeTab === 'alerts' && <AlertsTab />}
        {activeTab === 'settings' && <SettingsTab />}
      </main>

      {/* Bottom Navigation */}
      <BottomNav activeTab={activeTab} onTabChange={setActiveTab} />
    </div>
  )
}

// Header Component
function Header({ lastUpdate, onRefresh, loading }) {
  return (
    <header className="px-4 pt-4 pb-2">
      <div className="glass-card">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-primary-400 to-primary-600 bg-clip-text text-transparent">
              💰 VAlert
            </h1>
            <p className="text-sm text-dark-400 mt-1">
              Yangilangan: {lastUpdate.toLocaleTimeString('uz-UZ')}
            </p>
          </div>
          <button
            onClick={onRefresh}
            disabled={loading}
            className={`w-12 h-12 glass-button flex items-center justify-center text-xl
                       ${loading ? 'animate-spin' : ''}`}
          >
            🔄
          </button>
        </div>
      </div>
    </header>
  )
}

// Rates Tab
function RatesTab({ rates, loading }) {
  return (
    <div className="space-y-4">
      {/* Quick Stats */}
      <div className="grid grid-cols-2 gap-3">
        <QuickStat
          label="USD/UZS"
          value="12,720"
          change="+0.15%"
          positive={true}
        />
        <QuickStat
          label="EUR/UZS"
          value="13,870"
          change="-0.08%"
          positive={false}
        />
      </div>

      {/* Rates List */}
      <div className="space-y-3">
        <h2 className="text-lg font-semibold text-dark-200 flex items-center gap-2">
          <span>🏦</span> Barcha Kurslar
        </h2>

        {loading ? (
          // Skeleton Loading
          [1, 2, 3].map(i => (
            <div key={i} className="glass-card animate-pulse">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-dark-700"></div>
                <div className="flex-1 space-y-2">
                  <div className="h-4 w-20 bg-dark-700 rounded"></div>
                  <div className="h-3 w-32 bg-dark-700 rounded"></div>
                </div>
              </div>
            </div>
          ))
        ) : (
          rates.map((rate, i) => (
            <RateCard key={rate.code} rate={rate} delay={i * 0.1} />
          ))
        )}
      </div>
    </div>
  )
}

// Quick Stat Component
function QuickStat({ label, value, change, positive }) {
  return (
    <div className="glass-card">
      <p className="text-sm text-dark-400 mb-1">{label}</p>
      <p className="text-2xl font-bold text-white">{value}</p>
      <p className={`text-sm font-medium ${positive ? 'value-up' : 'value-down'}`}>
        {positive ? '📈' : '📉'} {change}
      </p>
    </div>
  )
}

// Rate Card Component
function RateCard({ rate, delay }) {
  const getCurrencyIcon = (code) => {
    const icons = { USD: '💵', EUR: '💶', RUB: '🪙', GBP: '💷', CNY: '🇨🇳' }
    return icons[code] || '💱'
  }

  return (
    <div
      className="rate-card animate-slide-up"
      style={{ animationDelay: `${delay}s` }}
    >
      <div className="flex items-center gap-4">
        {/* Currency Icon */}
        <div className={`currency-icon ${rate.code.toLowerCase()}`}>
          {getCurrencyIcon(rate.code)}
        </div>

        {/* Currency Info */}
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="font-bold text-white">{rate.code}</span>
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium
              ${rate.change >= 0 ? 'bg-accent-green/20 text-accent-green' : 'bg-accent-red/20 text-accent-red'}`}>
              {rate.change >= 0 ? '+' : ''}{rate.change}%
            </span>
          </div>
          <p className="text-sm text-dark-400">{rate.name}</p>
        </div>

        {/* Rates */}
        <div className="text-right">
          <div className="flex items-center gap-3 text-sm">
            <div>
              <p className="text-dark-400 text-xs">Sotib olish</p>
              <p className="font-semibold text-accent-green">{rate.buy.toLocaleString()}</p>
            </div>
            <div className="w-px h-8 bg-dark-600"></div>
            <div>
              <p className="text-dark-400 text-xs">Sotish</p>
              <p className="font-semibold text-accent-red">{rate.sell.toLocaleString()}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// Calculator Tab
function CalculatorTab({ rates }) {
  const [amount, setAmount] = useState('')
  const [fromCurrency, setFromCurrency] = useState('USD')
  const [toCurrency, setToCurrency] = useState('UZS')

  const getRate = (code) => rates.find(r => r.code === code)?.sell || 1

  const result = amount ? (parseFloat(amount) * getRate(fromCurrency)).toLocaleString() : '0'

  return (
    <div className="space-y-6 animate-slide-up">
      <div className="glass-card">
        <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
          <span>🧮</span> Valyuta Kalkulyatori
        </h2>

        {/* Amount Input */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-dark-400 mb-2">Miqdor</label>
            <input
              type="number"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="100"
              className="input-premium text-2xl font-bold"
            />
          </div>

          {/* Currency Selectors */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-dark-400 mb-2">Dan</label>
              <select
                value={fromCurrency}
                onChange={(e) => setFromCurrency(e.target.value)}
                className="input-premium"
              >
                <option value="USD">🇺🇸 USD</option>
                <option value="EUR">🇪🇺 EUR</option>
                <option value="RUB">🇷🇺 RUB</option>
                <option value="GBP">🇬🇧 GBP</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-dark-400 mb-2">Ga</label>
              <select
                value={toCurrency}
                onChange={(e) => setToCurrency(e.target.value)}
                className="input-premium"
              >
                <option value="UZS">🇺🇿 UZS</option>
              </select>
            </div>
          </div>

          {/* Result */}
          <div className="mt-6 p-6 bg-gradient-to-r from-primary-500/20 to-primary-600/20 rounded-xl border border-primary-500/30">
            <p className="text-sm text-dark-300 mb-2">Natija</p>
            <p className="text-3xl font-bold text-white">
              {result} <span className="text-lg text-dark-400">so'm</span>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

// Alerts Tab
function AlertsTab() {
  const [alerts] = useState([
    { id: 1, currency: 'USD', type: 'above', value: 13000, active: true },
    { id: 2, currency: 'EUR', type: 'below', value: 13500, active: false },
  ])

  return (
    <div className="space-y-6 animate-slide-up">
      <div className="glass-card">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <span>🔔</span> Alertlarim
          </h2>
          <button className="btn-primary text-sm py-2">
            ➕ Yangi
          </button>
        </div>

        {alerts.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-6xl mb-4">📭</p>
            <p className="text-dark-400">Hali alertlar yo'q</p>
          </div>
        ) : (
          <div className="space-y-3">
            {alerts.map(alert => (
              <div key={alert.id} className="flex items-center justify-between p-4 bg-dark-800/50 rounded-xl">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">
                    {alert.type === 'above' ? '📈' : '📉'}
                  </span>
                  <div>
                    <p className="font-semibold text-white">
                      {alert.currency} {alert.type === 'above' ? '>' : '<'} {alert.value.toLocaleString()}
                    </p>
                    <p className="text-sm text-dark-400">
                      {alert.active ? '🟢 Faol' : '⏸️ To\'xtatilgan'}
                    </p>
                  </div>
                </div>
                <button className="p-2 hover:bg-dark-700 rounded-lg transition-colors">
                  🗑️
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// Settings Tab
function SettingsTab() {
  const [notifications, setNotifications] = useState(true)
  const [dailyReport, setDailyReport] = useState(false)

  return (
    <div className="space-y-6 animate-slide-up">
      <div className="glass-card">
        <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
          <span>⚙️</span> Sozlamalar
        </h2>

        <div className="space-y-4">
          <SettingItem
            icon="🔔"
            title="Bildirishnomalar"
            description="Alert triggerlarida xabar olish"
            enabled={notifications}
            onChange={setNotifications}
          />
          <SettingItem
            icon="📅"
            title="Kunlik hisobot"
            description="Har kuni ertalab kurs xulosasi"
            enabled={dailyReport}
            onChange={setDailyReport}
          />
        </div>
      </div>

      {/* About Section */}
      <div className="glass-card">
        <h3 className="font-semibold text-white mb-4">Haqida</h3>
        <div className="space-y-2 text-sm text-dark-400">
          <p>📱 VAlert v2.0</p>
          <p>👨‍💻 Azamat Qalmuratov</p>
          <p>🌐 O'zbekiston bank kurslari</p>
        </div>
      </div>
    </div>
  )
}

// Setting Item Component
function SettingItem({ icon, title, description, enabled, onChange }) {
  return (
    <div className="flex items-center justify-between p-4 bg-dark-800/50 rounded-xl">
      <div className="flex items-center gap-3">
        <span className="text-2xl">{icon}</span>
        <div>
          <p className="font-medium text-white">{title}</p>
          <p className="text-sm text-dark-400">{description}</p>
        </div>
      </div>
      <button
        onClick={() => onChange(!enabled)}
        className={`w-14 h-8 rounded-full transition-all duration-200 relative
          ${enabled ? 'bg-primary-500' : 'bg-dark-600'}`}
      >
        <span className={`absolute top-1 w-6 h-6 bg-white rounded-full transition-all duration-200 shadow-lg
          ${enabled ? 'left-7' : 'left-1'}`}></span>
      </button>
    </div>
  )
}

// Bottom Navigation
function BottomNav({ activeTab, onTabChange }) {
  return (
    <nav className="fixed bottom-0 left-0 right-0 px-4 pb-4 safe-area-bottom">
      <div className="glass p-2 flex items-center justify-around">
        {TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={`flex flex-col items-center gap-1 px-4 py-2 rounded-xl transition-all duration-200
              ${activeTab === tab.id
                ? 'bg-primary-500/20 text-primary-400'
                : 'text-dark-400 hover:text-white'}`}
          >
            <span className="text-xl">{tab.icon}</span>
            <span className="text-xs font-medium">{tab.label}</span>
          </button>
        ))}
      </div>
    </nav>
  )
}

export default App
