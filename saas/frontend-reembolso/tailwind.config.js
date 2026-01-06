/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Paleta "Dark Leather" (Masculina e Elegante)
        dark: {
          900: '#0f172a', // Fundo principal
          800: '#1e293b', // Paineis
          700: '#334155', // Bordas
        },
        brand: {
          500: '#d97706', // Laranja Queimado / Couro
          600: '#b45309',
        }
      }
    },
  },
  plugins: [],
}