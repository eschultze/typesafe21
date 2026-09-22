import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Noto_Sans_Symbols_2 } from "next/font/google";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const notoSymbols = Noto_Sans_Symbols_2({
  variable: "--font-symbols",
  subsets: ["latin"],
  weight: "400",
});

export const metadata: Metadata = {
  title: "TypeSafe21",
  description: "AI-powered Blackjack — three players, one shoe, zero mercy.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} ${notoSymbols.variable} h-full antialiased dark`}
      data-theme="midnight"
    >
      <body className="min-h-full flex flex-col bg-background text-foreground">
        <TooltipProvider>
          <ErrorBoundary>{children}</ErrorBoundary>
        </TooltipProvider>
      </body>
    </html>
  );
}
