export const metadata = {
  title: "Kyros Agent Console",
  description: "Web console for the Kyros agent orchestration platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}