/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        bloodline: {
          crimson: '#E5334F',
          dark: '#0B1220',
          navy: '#0F172A',
        }
      }
    },
  },
  plugins: [],
}
