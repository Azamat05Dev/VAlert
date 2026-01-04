/**
 * Onboarding Tutorial Component
 * Shows on first app launch to introduce features
 */
import { useState, useEffect } from 'react'

const SLIDES = [
    {
        icon: '💰',
        title: 'VAlert\'ga Xush Kelibsiz!',
        description: 'O\'zbekistondagi eng aniq valyuta kurslari ilovasi',
        color: '#0ea5e9',
    },
    {
        icon: '📊',
        title: 'Real-time Kurslar',
        description: 'CBU va barcha bank kurslarini real vaqtda kuzating',
        color: '#22c55e',
    },
    {
        icon: '📈',
        title: 'Interaktiv Grafiklar',
        description: 'Kurs tarixini grafik ko\'rinishda tahlil qiling',
        color: '#8b5cf6',
    },
    {
        icon: '🔔',
        title: 'Aqlli Alertlar',
        description: 'Kurs belgilangan qiymatga yetganda darhol xabar oling',
        color: '#f59e0b',
    },
    {
        icon: '🚀',
        title: 'Boshlash Tayyor!',
        description: 'Valyuta kurslarini kuzatishni boshlang',
        color: '#ef4444',
    },
]

export default function Onboarding({ onComplete }) {
    const [currentSlide, setCurrentSlide] = useState(0)
    const [touchStart, setTouchStart] = useState(0)
    const [touchEnd, setTouchEnd] = useState(0)

    const minSwipeDistance = 50

    const handleTouchStart = (e) => {
        setTouchEnd(0)
        setTouchStart(e.targetTouches[0].clientX)
    }

    const handleTouchMove = (e) => {
        setTouchEnd(e.targetTouches[0].clientX)
    }

    const handleTouchEnd = () => {
        if (!touchStart || !touchEnd) return

        const distance = touchStart - touchEnd
        const isLeftSwipe = distance > minSwipeDistance
        const isRightSwipe = distance < -minSwipeDistance

        if (isLeftSwipe && currentSlide < SLIDES.length - 1) {
            setCurrentSlide(prev => prev + 1)
        }
        if (isRightSwipe && currentSlide > 0) {
            setCurrentSlide(prev => prev - 1)
        }
    }

    const handleNext = () => {
        if (currentSlide < SLIDES.length - 1) {
            setCurrentSlide(prev => prev + 1)
        } else {
            localStorage.setItem('valert_onboarded', 'true')
            onComplete()
        }
    }

    const handleSkip = () => {
        localStorage.setItem('valert_onboarded', 'true')
        onComplete()
    }

    const slide = SLIDES[currentSlide]

    return (
        <div
            className="fixed inset-0 bg-dark-900 z-[200] flex flex-col"
            onTouchStart={handleTouchStart}
            onTouchMove={handleTouchMove}
            onTouchEnd={handleTouchEnd}
        >
            {/* Skip Button */}
            <div className="absolute top-6 right-6 z-10">
                <button
                    onClick={handleSkip}
                    className="text-dark-400 hover:text-white transition-colors px-4 py-2"
                >
                    O'tkazib yuborish →
                </button>
            </div>

            {/* Slide Content */}
            <div className="flex-1 flex flex-col items-center justify-center px-8">
                {/* Icon */}
                <div
                    className="w-32 h-32 rounded-3xl flex items-center justify-center mb-8 animate-bounce-slow"
                    style={{
                        backgroundColor: `${slide.color}20`,
                        boxShadow: `0 0 60px ${slide.color}40`
                    }}
                >
                    <span className="text-7xl">{slide.icon}</span>
                </div>

                {/* Title */}
                <h1
                    className="text-3xl font-bold text-white text-center mb-4 animate-fade-in"
                    key={`title-${currentSlide}`}
                >
                    {slide.title}
                </h1>

                {/* Description */}
                <p
                    className="text-lg text-dark-400 text-center max-w-sm animate-slide-up"
                    key={`desc-${currentSlide}`}
                >
                    {slide.description}
                </p>
            </div>

            {/* Navigation */}
            <div className="px-8 pb-12 space-y-6">
                {/* Dots */}
                <div className="flex justify-center gap-2">
                    {SLIDES.map((_, i) => (
                        <button
                            key={i}
                            onClick={() => setCurrentSlide(i)}
                            className={`transition-all duration-300 rounded-full
                ${i === currentSlide
                                    ? 'w-8 h-2'
                                    : 'w-2 h-2'}`}
                            style={{
                                backgroundColor: i === currentSlide ? slide.color : '#475569'
                            }}
                        />
                    ))}
                </div>

                {/* Action Button */}
                <button
                    onClick={handleNext}
                    className="w-full py-4 rounded-2xl font-semibold text-white text-lg transition-all transform hover:scale-[1.02] active:scale-[0.98]"
                    style={{
                        background: `linear-gradient(135deg, ${slide.color}, ${slide.color}cc)`,
                        boxShadow: `0 0 30px ${slide.color}40`
                    }}
                >
                    {currentSlide === SLIDES.length - 1 ? 'Boshlash 🚀' : 'Keyingisi →'}
                </button>
            </div>
        </div>
    )
}

// Check if should show onboarding
export function shouldShowOnboarding() {
    return !localStorage.getItem('valert_onboarded')
}
