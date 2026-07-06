import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "ArenaMind AI - Stadium OS",
  description: "The Intelligent Operating System for FIFA World Cup 2026 Stadiums",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-background text-zinc-100 antialiased">
        {children}
      </body>
    </html>
  );
}
