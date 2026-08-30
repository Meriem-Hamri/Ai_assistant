import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Assistant AI",
  description: "Assistant documentaire local",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  );
}
