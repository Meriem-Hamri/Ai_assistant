import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AssistantAI — Document intelligence",
  description: "Espace intelligent de gestion et d’interrogation documentaire",
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
