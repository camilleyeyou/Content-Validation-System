/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      borderRadius: {
        xl: "0.75rem",
        "2xl": "1rem",
      },
      boxShadow: {
        soft: "0 2px 14px 0 rgba(0,0,0,0.06)",
        hard: "0 4px 20px -4px rgba(0,0,0,0.18)",
      },
    },
  },
  plugins: [],
};
