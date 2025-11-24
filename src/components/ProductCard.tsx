// src/components/ProductCard.tsx
"use client";

import Image from "next/image";
import Link from "next/link";
import type { Producto } from "@/data/productos";
import { useCarrito } from "@/store/carrito";

export function ProductCard({ producto }: { producto: Producto }) {
  const { agregar } = useCarrito();

  return (
    <article className="group flex flex-col overflow-hidden rounded-2xl border bg-white shadow-sm transition hover:-translate-y-1 hover:shadow-lg">
      <Link href={`/producto/${producto.id}`}>
        <div className="relative h-48 w-full overflow-hidden">
          <Image
            src={producto.imagenUrl}
            alt={producto.nombre}
            fill
            className="object-cover transition-transform duration-300 group-hover:scale-105"
          />
        </div>
      </Link>

      <div className="p-4 flex flex-col gap-2">
        <span className="inline-flex w-fit rounded-full bg-pink-50 px-3 py-1 text-xs font-medium text-pink-600">
          {producto.categoria}
        </span>

        <h3 className="text-lg font-semibold text-slate-900">
          {producto.nombre}
        </h3>

        <p className="text-slate-600 text-sm">{producto.descripcion}</p>

        <p className="text-lg font-bold text-emerald-700">
          ${producto.precio}.00
        </p>

        <button
          onClick={() => agregar(producto)}
          className="mt-2 rounded-full bg-emerald-600 text-white px-4 py-2 text-sm font-semibold hover:bg-emerald-700 active:scale-95"
        >
          Agregar al carrito
        </button>
      </div>
    </article>
  );
}
