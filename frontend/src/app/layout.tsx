import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Travel AI Agent Platform',
  description: 'AI-powered travel planning and booking',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
