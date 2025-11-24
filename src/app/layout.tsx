// src/app/layout.tsx
import "./globals.css";
import Link from "next/link";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className="min-h-screen bg-white">
        {/* NAVBAR */}
        <header className="w-full border-b bg-white">
          <nav className="mx-auto max-w-6xl flex justify-between items-center px-6 py-4">
            <Link href="/" className="text-xl font-bold text-slate-800">
              Pastelería Abuelito
            </Link>

            <div className="flex items-center gap-4">
              <Link
                href="/catalogo"
                className="text-slate-700 hover:text-slate-900"
              >
                Catálogo
              </Link>

              {/* 👉 BOTÓN VER CARRITO */}
              <Link
                href="/carrito"
                className="rounded-full bg-emerald-600 text-white px-4 py-2 text-sm font-semibold hover:bg-emerald-700 active:scale-95"
              >
                Ver carrito
              </Link>
            </div>
          </nav>
        </header>

        {/* CONTENIDO */}
        <main>{children}</main>
      </body>
    </html>
  );
}

