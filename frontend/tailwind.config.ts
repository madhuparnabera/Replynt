import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}"
  ],
  theme: {
    extend: {
      colors: {
        canvas: "#0B0F17",
        panel: "#111827",
        line: "rgba(148, 163, 184, 0.16)"
      },
      boxShadow: {
        glow: "0 24px 80px rgba(37, 99, 235, 0.16)"
      }
    }
  },
  plugins: []
};

export default config;
