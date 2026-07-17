/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ocean: {
          50: "#effbff",
          100: "#dff6ff",
          500: "#0ea5c6",
          600: "#0786a5",
          700: "#0b6b84",
          900: "#123f4d"
        }
      },
      boxShadow: {
        soft: "0 20px 50px -24px rgba(8, 78, 100, 0.34)"
      }
    }
  },
  plugins: []
};
