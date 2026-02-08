/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                mainframe: {
                    bg: "#09090b", // Zinc 950
                    card: "#18181b", // Zinc 900
                    border: "#27272a", // Zinc 800
                    accent: "#22d3ee", // Cyan 400
                    text: "#e4e4e7", // Zinc 200
                }
            },
            fontFamily: {
                mono: ['"JetBrains Mono"', 'monospace'],
                sans: ['Inter', 'sans-serif'],
            }
        },
    },
    plugins: [],
}
