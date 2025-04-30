module.exports = {
  // ...existing config...
  theme: {
    extend: {
      // ...existing extensions...
      animation: {
        "spin-slow": "spin 3s linear infinite",
        "loading-bar": "loading 2s ease-in-out infinite",
      },
      keyframes: {
        loading: {
          "0%": { transform: "translateX(-100%)" },
          "100%": { transform: "translateX(100%)" },
        },
      },
    },
  },
};
