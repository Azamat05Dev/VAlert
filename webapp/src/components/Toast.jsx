/**
 * Toast Notification Component - Premium Version
 * Shows success, info, warning, error messages with animations
 */
export default function Toast({ message, type = 'info' }) {
    const styles = {
        success: 'bg-gradient-to-r from-emerald-500/20 to-green-500/20 border-l-4 border-accent-green text-accent-green shadow-lg shadow-accent-green/20',
        error: 'bg-gradient-to-r from-red-500/20 to-rose-500/20 border-l-4 border-accent-red text-accent-red shadow-lg shadow-accent-red/20',
        warning: 'bg-gradient-to-r from-amber-500/20 to-orange-500/20 border-l-4 border-amber-500 text-amber-400 shadow-lg shadow-amber-500/20',
        info: 'bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border-l-4 border-primary-500 text-primary-400 shadow-lg shadow-primary-500/20',
    }

    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️',
    }

    return (
        <div className="fixed top-20 left-4 right-4 z-[100] animate-slide-down">
            <div className={`glass backdrop-blur-xl p-4 rounded-xl flex items-center gap-3 ${styles[type]}`}>
                <span className="text-2xl animate-scale-pop">{icons[type]}</span>
                <p className="font-semibold">{message}</p>
            </div>
        </div>
    )
}
