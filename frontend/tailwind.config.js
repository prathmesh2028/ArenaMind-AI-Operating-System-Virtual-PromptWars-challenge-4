/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#09090b", // Sleek dark zinc background
        card: "#18181b",       // Darker card background
        primary: {
          DEFAULT: "#6366f1",  // Indigo
          dark: "#4f46e5",
          light: "#818cf8"
        },
        success: {
          DEFAULT: "#10b981",  // Emerald for safe status
          dark: "#059669",
          light: "#34d399"
        },
        warning: {
          DEFAULT: "#f59e0b",  // Amber for warnings/predictions
          dark: "#d97706",
          light: "#fbbf24"
        },
        danger: {
          DEFAULT: "#f43f5e",  // Rose for emergencies/incidents
          dark: "#e11d48",
          light: "#fb7185"
        },
        muted: "#71717a",      // Muted zinc grey
        border: "#27272a"      // Border lines
      },
      fontFamily: {
        sans: ["var(--font-sans)", "Inter", "sans-serif"],
      },
    },
  },
  plugins: [],
};
