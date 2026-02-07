import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      screens: {
        xs: "375px",  // Mobile
        sm: "640px",  // Large mobile
        md: "768px",  // Tablet
        lg: "1024px", // Desktop
      },
      colors: {
        "citation-badge-hover": "var(--citation-badge-hover)",
        "citation-badge-active": "var(--citation-badge-active)",
        "citation-badge-text": "var(--citation-badge-text)",
        "citation-link": "var(--citation-link)",
      },
      padding: {
        safe: "env(safe-area-inset-bottom)",
      },
    },
  },
  plugins: [],
};
export default config;
