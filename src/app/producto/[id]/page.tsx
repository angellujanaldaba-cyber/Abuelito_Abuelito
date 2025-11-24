// src/app/producto/[id]/page.tsx
"use client";

import Image from "next/image";
import { useParams } from "next/navigation";
import { productos } from "@/data/productos";
import { useCarrito } from "@/store/carrito";

export default function ProductoPage() {
  const params = useParams<{ id: string }>();
  const id = Number(params.id);

  const producto = productos.find((p) => p.id === id);

  if (!producto) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <h1 className="text-2xl font-bold text-red-600">
          Producto no encontrado
        </h1>
      </main>
    );
  }

  const { agregar } = useCarrito();

  const precioMXN = producto.precio.toLocaleString("es-MX", {
    style: "currency",
    currency: "MXN",
  });

  return (
    <main className="min-h-screen bg-slate-50 py-10">
      <section className="mx-auto max-w-5xl px-4 flex flex-col md:flex-row gap-10">
        {/* Imagen */}
        <div className="relative w-full md:w-1/2 h-80 md:h-[450px] rounded-2xl overflow-hidden shadow-sm">
          <Image
            src={producto.imagenUrl}
            alt={producto.nombre}
            fill
            className="object-cover"
          />
        </div>

        {/* Información */}
        <div className="flex-1 space-y-6">
          <span className="inline-flex w-fit rounded-full bg-pink-50 px-3 py-1 text-xs font-medium text-pink-700">
            {producto.categoria}
          </span>

          <h1 className="text-3xl font-bold text-slate-900">
            {producto.nombre}
          </h1>

          <p className="text-slate-600 text-sm leading-relaxed">
            {producto.descripcion}
          </p>

          <p className="text-2xl font-bold text-emerald-700">{precioMXN}</p>

          <button
            onClick={() => agregar(producto)}
            className="rounded-full bg-emerald-600 text-white px-6 py-3 text-sm font-semibold shadow-md hover:bg-emerald-700 active:scale-95"
          >
            Agregar al carrito
          </button>
        </div>
      </section>
    </main>
  );
}
