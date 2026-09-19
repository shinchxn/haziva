import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Haziva - Risk & Relocation Intelligence",
  description: "AI-powered habitation risk and relocation intelligence system",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
