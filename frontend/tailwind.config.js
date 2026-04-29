/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0B0E14',
        surface: '#151A23',
        primary: '#00FF41',
        textPrimary: '#E0E0E0'
      }
    },
  },
  plugins: [],
}