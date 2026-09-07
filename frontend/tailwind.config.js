/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        cyber: {
          bg: "#070b12",
          surface: "#0d1524",
          card: "rgba(13, 21, 36, 0.75)",
          border: "rgba(6, 182, 212, 0.2)",
          cyan: "#06b6d4",
          cyanGlow: "rgba(6, 182, 212, 0.4)",
          emerald: "#10b981",
          emeraldGlow: "rgba(16, 185, 129, 0.4)",
          crimson: "#ef4444",
          crimsonGlow: "rgba(239, 68, 68, 0.4)",
          amber: "#f59e0b",
          purple: "#8b5cf6",
          blue: "#3b82f6",
        },
      },
      fontFamily: {
        mono: [
          "JetBrains Mono",
          "Fira Code",
          "Roboto Mono",
          "ui-monospace",
          "monospace",
        ],
        sans: [
          "Inter",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
      },
      animation: {
        "radar-sweep": "radarSweep 4s linear infinite",
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "scan-line": "scanline 2.5s ease-in-out infinite",
        "glow": "glowPulse 2s ease-in-out infinite alternate",
        "merkle-flow": "flowDash 1.5s linear infinite",
      },
      keyframes: {
        radarSweep: {
          "0%": { transform: "rotate(0deg)" },
          "100%": { transform: "rotate(360deg)" },
        },
        scanline: {
          "0%, 100%": { top: "0%" },
          "50%": { top: "95%" },
        },
        glowPulse: {
          "0%": { filter: "drop-shadow(0 0 4px rgba(6, 182, 212, 0.4))" },
          "100%": { filter: "drop-shadow(0 0 16px rgba(6, 182, 212, 0.8))" },
        },
        flowDash: {
          to: { strokeDashoffset: "-20" },
        },
      },
      boxShadow: {
        "cyber-cyan": "0 0 20px -3px rgba(6, 182, 212, 0.35)",
        "cyber-emerald": "0 0 20px -3px rgba(16, 185, 129, 0.35)",
        "cyber-crimson": "0 0 20px -3px rgba(239, 68, 68, 0.45)",
        "cyber-card": "0 8px 32px 0 rgba(0, 0, 0, 0.5), inset 0 0 0 1px rgba(6, 182, 212, 0.15)",
        "cyber-card-active": "0 8px 32px 0 rgba(6, 182, 212, 0.2), inset 0 0 0 1px rgba(6, 182, 212, 0.4)",
        "cyber-card-alert": "0 8px 32px 0 rgba(239, 68, 68, 0.25), inset 0 0 0 1px rgba(239, 68, 68, 0.5)",
      },
    },
  },
  plugins: [],
};
