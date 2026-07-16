import './globals.css';

export const metadata = {
  title: 'AI Civilization Builder - Multiverse Simulator',
  description: 'An open-source simulation system featuring persistent AI agent grids, pricing markets, and branching history timelines.',
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
