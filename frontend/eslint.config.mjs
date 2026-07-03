import nextConfig from "eslint-config-next";

const eslintConfig = [
  ...nextConfig,
  {
    rules: {
      // Flags the standard fetch-on-mount pattern used across this app's pages;
      // keep as a warning rather than disabling the check entirely.
      "react-hooks/set-state-in-effect": "warn",
    },
  },
];

export default eslintConfig;
