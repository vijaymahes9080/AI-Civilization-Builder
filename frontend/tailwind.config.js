/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0d0f12",
        panel: "#181b20",
        primary: "#3b82f6",
        accent: "#10b981",
      }
    },
  },
  plugins: [],
}
