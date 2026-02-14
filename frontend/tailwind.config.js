/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                background: "#0e1117",
                surface: "#1e2127",
                border: "#2e3137",
                primary: "#3b82f6",
                success: "#10b981",          // Updated to emerald-500 equivalent
                error: "#ff4b4b",
                danger: "#ff4b4b",           // Added alias for 'danger' class usage
                "card-purple": "#8b5cf61a",  // violet-500 with opacity
                "card-blue": "#3b82f61a",    // blue-500 with opacity
                "card-green": "#10b9811a",   // emerald-500 with opacity
                "card-orange": "#f973161a",  // orange-500 with opacity
                "card-red": "#ef44441a",     // red-500 with opacity
            },
        },
    },
    plugins: [],
}
