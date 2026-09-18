/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          bg: "#070a12",
          card: "rgba(13, 20, 38, 0.55)",
          border: "rgba(255, 255, 255, 0.08)",
        },
        accent: {
          cyan: "#00f2fe",
          blue: "#4facfe",
          neon: "#05ffd5",
        },
        status: {
          vacant: "#10b981",
          occupied: "#f43f5e",
          reserved: "#3b82f6",
          ev: "#fbbf24",
        }
      },
      fontFamily: {
        sans: ['Inter', 'Outfit', 'sans-serif'],
      },
      animation: {
        'pulse-glow': 'pulseGlow 2s infinite alternate',
      },
      keyframes: {
        pulseGlow: {
          '0%': { boxShadow: '0 0 10px rgba(0, 242, 254, 0.2)' },
          '100%': { boxShadow: '0 0 25px rgba(0, 242, 254, 0.6)' },
        }
      }
    },
  },
  plugins: [],
}
