// src/app/page.tsx
import Link from "next/link";
import { productos } from "@/data/productos";
import { ProductCard } from "@/components/ProductCard";

export default function HomePage() {
  const destacados = productos.slice(0, 3);

  return (
    <main className="px-6 py-10 max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Pastelería Abuelito Abuelito</h1>
      <p className="text-slate-600 mb-8">
        Los pasteles más ricos hechos con amor y tradición 🍰.
      </p>

      {/* 🔥 BOTÓN PARA ABRIR EL CARRITO SIN RECARGAR */}
      <Link
        href="/carrito"
        className="inline-flex mb-10 rounded-full bg-emerald-600 text-white px-5 py-2 text-sm font-semibold hover:bg-emerald-700"
      >
        Ver carrito
      </Link>

      {/* Productos destacados */}
      <section>
        <h2 className="text-2xl font-bold mb-4">Destacados</h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {destacados.map((producto) => (
            <ProductCard key={producto.id} producto={producto} />
          ))}
        </div>
      </section>

      {/* Botón para ir al catálogo */}
      <div className="mt-10">
        <Link
          href="/catalogo"
          className="inline-flex rounded-full bg-pink-600 text-white px-6 py-3 text-sm font-semibold hover:bg-pink-700"
        >
          Ver catálogo completo
        </Link>
      </div>
    </main>
  );
}
