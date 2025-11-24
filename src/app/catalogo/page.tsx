"use client";

import { useState } from "react";
import { productos, CategoriaProducto } from "@/data/productos";
import { ProductCard } from "@/components/ProductCard";

const categorias: (CategoriaProducto | "Todos")[] = [
  "Todos",
  "Clásicos",
  "Cumpleaños",
  "Infantiles",
  "Bodas",
];

export default function CatalogoPage() {
  const [categoriaActiva, setCategoriaActiva] =
    useState<CategoriaProducto | "Todos">("Todos");

  const productosFiltrados =
    categoriaActiva === "Todos"
      ? productos
      : productos.filter((p) => p.categoria === categoriaActiva);

  return (
    <main className="min-h-screen bg-slate-50">
      <section className="mx-auto max-w-6xl px-4 pb-16 pt-10">
        <header className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
              Catálogo de pasteles
            </h1>
            <p className="mt-1 text-sm text-slate-600">
              Elige tu pastel ideal por categoría: clásicos, cumpleaños,
              infantiles o bodas.
            </p>
          </div>

          {/* Filtro por categoría */}
          <div className="flex flex-wrap gap-2">
            {categorias.map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => setCategoriaActiva(cat)}
                className={`rounded-full border px-3 py-1 text-xs font-medium transition ${
                  categoriaActiva === cat
                    ? "border-emerald-600 bg-emerald-600 text-white"
                    : "border-slate-200 bg-white text-slate-700 hover:border-emerald-300"
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </header>

        {/* Grid de productos */}
        {productosFiltrados.length === 0 ? (
          <p className="text-sm text-slate-500">
            No hay productos en esta categoría por ahora.
          </p>
        ) : (
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {productosFiltrados.map((prod) => (
              <ProductCard key={prod.id} producto={prod} />
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
