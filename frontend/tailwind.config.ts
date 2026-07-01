import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eff6ff",
          100: "#dbeafe",
          500: "#3b82f6",
          600: "#2563eb",
          700: "#1d4ed8",
          900: "#1e3a5f",
        },
      },
      animation: {
        "bounce-dot": "bounceDot 1.2s infinite ease-in-out",
      },
      keyframes: {
        bounceDot: {
          "0%, 80%, 100%": { transform: "scale(0)", opacity: "0.3" },
          "40%": { transform: "scale(1.0)", opacity: "1" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
