import type { NextConfig } from "next";

const backendInternalUrl = process.env.BACKEND_INTERNAL_URL;

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    if (!backendInternalUrl) {
      return [];
    }
    return [
      {
        source: "/api/:path*",
        destination: `${backendInternalUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
