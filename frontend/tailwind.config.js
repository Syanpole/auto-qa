export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        steel: "#1f3a5f",
        copper: "#b66535",
        mint: "#00a38c",
        fog: "#f3f5f8",
      },
      fontFamily: {
        headline: ["Manrope", "sans-serif"],
        body: ["IBM Plex Sans", "sans-serif"],
      }
    }
  },
  plugins: []
};
