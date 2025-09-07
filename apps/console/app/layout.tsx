import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Kyros Console",
  description: "Local-first agent console",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body style={{ minHeight: "100vh", margin: 0 }}>
        <main>{children}</main>
      </body>
    </html>
  );
}
