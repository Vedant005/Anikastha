import type { NextConfig } from "next";

const isStandalone = process.env.NEXT_OUTPUT === "standalone";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  ...(isStandalone ? { output: "standalone" as const } : {}),
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: "http://127.0.0.1:8000/api/v1/:path*",
      },
    ];
  },
};

export default nextConfig;
