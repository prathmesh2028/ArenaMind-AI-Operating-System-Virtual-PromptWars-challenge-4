/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  eslint: {
    // Enable lint checks but do not block build on warning during development checks
    ignoreDuringBuilds: false,
  },
  images: {
    unoptimized: true, // Useful for Docker builds and export stages
  },
}

module.exports = nextConfig
