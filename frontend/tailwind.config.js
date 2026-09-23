/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Menlo', 'Monaco', 'Courier New', 'monospace'],
      },
      colors: {
        background: {
          light: '#F8FAFC',
          dark: '#090A0F',
          cardLight: '#FFFFFF',
          cardDark: '#12141C',
          subtleDark: '#181B26',
        },
        border: {
          light: '#E2E8F0',
          dark: '#222738',
        },
        accent: {
          green: '#10B981',
          greenBg: 'rgba(16, 185, 129, 0.12)',
          red: '#F43F5E',
          redBg: 'rgba(244, 63, 94, 0.12)',
          amber: '#F59E0B',
          amberBg: 'rgba(245, 158, 11, 0.12)',
          blue: '#3B82F6',
          blueBg: 'rgba(59, 130, 246, 0.12)',
          purple: '#8B5CF6',
          purpleBg: 'rgba(139, 92, 246, 0.12)',
        }
      },
      boxShadow: {
        'subtle': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        'premium': '0 4px 20px -2px rgba(0, 0, 0, 0.25)',
        'glow-green': '0 0 15px rgba(16, 185, 129, 0.25)',
        'glow-blue': '0 0 15px rgba(59, 130, 246, 0.25)',
      }
    },
  },
  plugins: [],
}
