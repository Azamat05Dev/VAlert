import { useState, useEffect, useCallback } from 'react'
import './index.css'
import ChartTab from './components/ChartTab'
import AlertForm from './components/AlertForm'

// Telegram WebApp API
const tg = window.Telegram?.WebApp

// Real-time rates (mock - will be replaced with API)
const MOCK_RATES = [
  { code: 'USD', name: 'AQSh Dollari', buy: 12680, sell: 12750, change: 0.15, official: 12720 },
  { code: 'EUR', name: 'Yevro', buy: 13820, sell: 13920, change: -0.08, official: 13870 },
  { code: 'RUB', name: 'Rossiya Rubli', buy: 127.5, sell: 129.8, change: 0.25, official: 128.2 },
  { code: 'GBP', name: 'Funt Sterling', buy: 16100, sell: 16250, change: 0.12, official: 16180 },
  { code: 'CNY', name: 'Xitoy Yuani', buy: 1745, sell: 1768, change: -0.05, official: 1752 },
]

// Tab definitions with new Charts tab
const TABS = [
  { id: 'rates', icon: '📊', label: 'Kurslar' },
  { id: 'charts', icon: '📈', label: 'Grafik' },
  { id: 'calc', icon: '🧮', label: 'Kalkul.' },
  { id: 'alerts', icon: '🔔', label: 'Alertlar' },
]

function App() {
  const [activeTab, setActiveTab] = useState('rates')
  const [rates, setRates] = useState(MOCK_RATES)
  const [loading, setLoading] = useState(false)
  const [lastUpdate, setLastUpdate] = useState(new Date())
  const [showAlertForm, setShowAlertForm] = useState(false)
  const [pullDistance, setPullDistance] = useState(0)

  useEffect(() => {
    // Initialize Telegram WebApp
    if (tg) {
      tg.ready()
      tg.expand()
      tg.setHeaderColor('#0f172a')
      tg.setBackgroundColor('#0f172a')

      // Enable closing confirmation
      tg.enableClosingConfirmation()
    }
  }, [])

  // Haptic feedback helper
  const haptic = useCallback((type = 'light') => {
    tg?.HapticFeedback?.impactOccurred(type)
  }, [])

  const refreshRates = async () => {
    haptic('medium')
    setLoading(true)

    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 800))

    // Simulate small rate changes
    setRates(prev => prev.map(r => ({
      ...r,
      buy: r.buy + (Math.random() - 0.5) * 10,
      sell: r.sell + (Math.random() - 0.5) * 10,
      change: parseFloat((r.change + (Math.random() - 0.5) * 0.1).toFixed(2)),
    })))

    setLastUpdate(new Date())
    setLoading(false)
    haptic('light')
  }

  // Pull to refresh handler
  const handleTouchStart = (e) => {
    if (window.scrollY === 0) {
      const touch = e.touches[0]
      window._pullStartY = touch.clientY
    }
  }

  const handleTouchMove = (e) => {
    if (window._pullStartY && window.scrollY === 0) {
      const touch = e.touches[0]
      const diff = touch.clientY - window._pullStartY
      if (diff > 0 && diff < 150) {
        setPullDistance(diff)
      }
    }
  }

  const handleTouchEnd = () => {
    if (pullDistance > 80) {
      refreshRates()
    }
    setPullDistance(0)
    window._pullStartY = null
  }

  const handleTabChange = (tabId) => {
    haptic('light')
    setActiveTab(tabId)
  }

  const handleCreateAlert = async (alertData) => {
    console.log('Creating alert:', alertData)
    haptic('success')
    // In production: call API
  }

  return (
    <div
      className="min-h-screen pb-24 safe-area-top safe-area-bottom"
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
    >
      {/* Pull to Refresh Indicator */}
      {pullDistance > 0 && (
        <div
          className="fixed top-0 left-0 right-0 flex justify-center items-center z-50 transition-all"
          style={{ height: pullDistance, opacity: pullDistance / 80 }}
        >
          <div className={`w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full
            ${pullDistance > 80 ? 'animate-spin' : ''}`}
          ></div>
        </div>
      )}

      {/* Header */}
      <Header lastUpdate={lastUpdate} onRefresh={refreshRates} loading={loading} />

      {/* Main Content with Page Transitions */}
      <main className="px-4 py-6">
        <div key={activeTab} className="animate-fade-in">
          {activeTab === 'rates' && <RatesTab rates={rates} loading={loading} />}
          {activeTab === 'charts' && <ChartTab />}
          {activeTab === 'calc' && <CalculatorTab rates={rates} />}
          {activeTab === 'alerts' && <AlertsTab onNewAlert={() => setShowAlertForm(true)} />}
        </div>
      </main>

      {/* Bottom Navigation */}
      <BottomNav activeTab={activeTab} onTabChange={handleTabChange} />

      {/* Alert Form Modal */}
      {showAlertForm && (
        <AlertForm
          onClose={() => setShowAlertForm(false)}
          onSubmit={handleCreateAlert}
        />
      )}
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
              {lastUpdate.toLocaleTimeString('uz-UZ')}
            </p>
          </div>
          <button
            onClick={onRefresh}
            disabled={loading}
            className="w-12 h-12 glass-button flex items-center justify-center text-xl ripple"
          >
            <span className={loading ? 'animate-spin' : ''}>🔄</span>
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
          value={rates[0]?.official?.toLocaleString() || '12,720'}
          change={`${rates[0]?.change >= 0 ? '+' : ''}${rates[0]?.change}%`}
          positive={rates[0]?.change >= 0}
        />
        <QuickStat
          label="EUR/UZS"
          value={rates[1]?.official?.toLocaleString() || '13,870'}
          change={`${rates[1]?.change >= 0 ? '+' : ''}${rates[1]?.change}%`}
          positive={rates[1]?.change >= 0}
        />
      </div>

      {/* Rates List */}
      <div className="space-y-3">
        <h2 className="text-lg font-semibold text-dark-200 flex items-center gap-2">
          <span>🏦</span> Barcha Kurslar
        </h2>

        {loading ? (
          [1, 2, 3].map(i => (
            <div key={i} className="glass-card">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-dark-700 animate-pulse"></div>
                <div className="flex-1 space-y-2">
                  <div className="h-4 w-20 bg-dark-700 rounded animate-pulse"></div>
                  <div className="h-3 w-32 bg-dark-700 rounded animate-pulse"></div>
                </div>
              </div>
            </div>
          ))
        ) : (
          rates.map((rate, i) => (
            <RateCard key={rate.code} rate={rate} delay={i * 0.05} />
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
      <p className={`text-sm font-medium ${positive ? 'text-accent-green' : 'text-accent-red'}`}>
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
      className="rate-card"
      style={{ animationDelay: `${delay}s` }}
    >
      <div className="flex items-center gap-4">
        <div className={`currency-icon ${rate.code.toLowerCase()}`}>
          {getCurrencyIcon(rate.code)}
        </div>

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

        <div className="text-right">
          <div className="flex items-center gap-3 text-sm">
            <div>
              <p className="text-dark-400 text-xs">Olish</p>
              <p className="font-semibold text-accent-green">{Math.round(rate.buy).toLocaleString()}</p>
            </div>
            <div className="w-px h-8 bg-dark-600"></div>
            <div>
              <p className="text-dark-400 text-xs">Sotish</p>
              <p className="font-semibold text-accent-red">{Math.round(rate.sell).toLocaleString()}</p>
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
  const [direction, setDirection] = useState('buy') // buy or sell

  const getRate = (code, dir) => {
    const r = rates.find(r => r.code === code)
    return dir === 'buy' ? r?.sell : r?.buy || 1
  }

  const rate = getRate(fromCurrency, direction)
  const result = amount ? (parseFloat(amount) * rate) : 0

  return (
    <div className="space-y-6">
      <div className="glass-card">
        <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
          <span>🧮</span> Valyuta Kalkulyatori
        </h2>

        <div className="space-y-4">
          {/* Amount Input */}
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

          {/* Currency Selector */}
          <div>
            <label className="block text-sm text-dark-400 mb-2">Valyuta</label>
            <div className="grid grid-cols-4 gap-2">
              {['USD', 'EUR', 'RUB', 'GBP'].map(c => (
                <button
                  key={c}
                  onClick={() => setFromCurrency(c)}
                  className={`py-3 rounded-xl font-semibold transition-all
                    ${fromCurrency === c
                      ? 'bg-primary-500 text-white shadow-glow'
                      : 'bg-dark-700/50 text-dark-400 hover:text-white'}`}
                >
                  {c}
                </button>
              ))}
            </div>
          </div>

          {/* Direction */}
          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={() => setDirection('buy')}
              className={`py-3 rounded-xl font-medium transition-all
                ${direction === 'buy'
                  ? 'bg-accent-green/20 text-accent-green border-2 border-accent-green'
                  : 'bg-dark-700/50 text-dark-400 border-2 border-transparent'}`}
            >
              💵 Sotib olish
            </button>
            <button
              onClick={() => setDirection('sell')}
              className={`py-3 rounded-xl font-medium transition-all
                ${direction === 'sell'
                  ? 'bg-accent-red/20 text-accent-red border-2 border-accent-red'
                  : 'bg-dark-700/50 text-dark-400 border-2 border-transparent'}`}
            >
              💰 Sotish
            </button>
          </div>

          {/* Result */}
          <div className="mt-6 p-6 bg-gradient-to-r from-primary-500/20 to-primary-600/20 rounded-xl border border-primary-500/30">
            <p className="text-sm text-dark-300 mb-2">Natija</p>
            <p className="text-3xl font-bold text-white">
              {result.toLocaleString('uz-UZ', { maximumFractionDigits: 0 })}
              <span className="text-lg text-dark-400 ml-2">so'm</span>
            </p>
            <p className="text-xs text-dark-400 mt-2">
              1 {fromCurrency} = {rate.toLocaleString()} so'm ({direction === 'buy' ? 'sotib olish' : 'sotish'})
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

// Alerts Tab
function AlertsTab({ onNewAlert }) {
  const [alerts] = useState([
    { id: 1, currency: 'USD', direction: 'above', threshold: 13000, active: true },
    { id: 2, currency: 'EUR', direction: 'below', threshold: 13500, active: false },
  ])

  return (
    <div className="space-y-6">
      <div className="glass-card">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <span>🔔</span> Alertlarim
          </h2>
          <button onClick={onNewAlert} className="btn-primary text-sm py-2 px-4">
            ➕ Yangi
          </button>
        </div>

        {alerts.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-6xl mb-4">📭</p>
            <p className="text-dark-400 mb-4">Hali alertlar yo'q</p>
            <button onClick={onNewAlert} className="btn-primary">
              Birinchi alertni yarating
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {alerts.map(alert => (
              <div key={alert.id} className="flex items-center justify-between p-4 bg-dark-800/50 rounded-xl">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">
                    {alert.direction === 'above' ? '📈' : '📉'}
                  </span>
                  <div>
                    <p className="font-semibold text-white">
                      {alert.currency} {alert.direction === 'above' ? '>' : '<'} {alert.threshold.toLocaleString()}
                    </p>
                    <p className={`text-sm ${alert.active ? 'text-accent-green' : 'text-dark-400'}`}>
                      {alert.active ? '🟢 Faol' : '⏸️ To\'xtatilgan'}
                    </p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button className="p-2 hover:bg-dark-700 rounded-lg transition-colors text-dark-400 hover:text-white">
                    {alert.active ? '⏸️' : '▶️'}
                  </button>
                  <button className="p-2 hover:bg-dark-700 rounded-lg transition-colors text-dark-400 hover:text-accent-red">
                    🗑️
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
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
            className={`flex flex-col items-center gap-1 px-3 py-2 rounded-xl transition-all
              ${activeTab === tab.id
                ? 'bg-primary-500/20 text-primary-400 scale-105'
                : 'text-dark-400 hover:text-white active:scale-95'}`}
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
