/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Do NOT put experimental.appDir here on Next 14+
  // Optional: helps in container builds, harmless locally
  output: 'standalone'
};

module.exports = nextConfig;
