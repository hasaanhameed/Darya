import type { Metadata } from "next";
import { IBM_Plex_Sans } from "next/font/google";

import { Providers } from "@/app/providers";
import { DisclaimerBar } from "@/components/layout/DisclaimerBar";
import { SampleDataBanner } from "@/components/layout/SampleDataBanner";
import { SiteHeader } from "@/components/layout/SiteHeader";
import "./globals.css";

const plexSans = IBM_Plex_Sans({
  variable: "--font-plex-sans",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  title: "Darya",
  description: "Flood monitoring and 1 to 3 day forecasts for the rivers of the Indus system. Research prototype.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${plexSans.variable} h-full`}>
      <body className="flex h-full flex-col font-sans">
        <SampleDataBanner />
        <SiteHeader />
        <DisclaimerBar />
        <Providers>
          <main className="flex min-h-0 flex-1 flex-col">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
