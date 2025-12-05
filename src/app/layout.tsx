// src/app/layout.tsx
import "./globals.css";
import { Header } from "@/components/Header";

export const metadata = {
  title: "Pastelería Abuelito",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className="bg-slate-50">
        <Header />
        <main className="pt-6">{children}</main>
      </body>
    </html>
  );
}
