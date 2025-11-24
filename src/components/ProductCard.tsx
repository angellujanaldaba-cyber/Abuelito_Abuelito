// components/ProductCard.tsx
import Image from "next/image";
import { Producto } from "@/data/productos";

interface ProductCardProps {
  producto: Producto;
}

export function ProductCard({ producto }: ProductCardProps) {
  const precioMXN = producto.precio.toLocaleString("es-MX", {
    style: "currency",
    currency: "MXN",
  });

  return (
    <article className="group flex flex-col overflow-hidden rounded-2xl border bg-white shadow-sm transition hover:-translate-y-1 hover:shadow-lg">
      <div className="relative h-48 w-full overflow-hidden">
        <Image
          src={producto.imagenUrl}
          alt={producto.nombre}
          fill
          className="object-cover transition duration-300 group-hover:scale-105"
        />
      </div>

      <div className="flex flex-1 flex-col gap-2 p-4">
        <span className="inline-flex w-fit rounded-full bg-pink-50 px-3 py-1 text-xs font-medium text-pink-700">
          {producto.categoria}
        </span>

        <h3 className="text-lg font-semibold text-slate-900">
          {producto.nombre}
        </h3>

        <p className="line-clamp-2 text-sm text-slate-600">
          {producto.descripcion}
        </p>

        <div className="mt-auto flex items-center justify-between pt-2">
          <span className="text-base font-bold text-emerald-700">
            {precioMXN}
          </span>
          <button
            className="rounded-full px-4 py-2 text-xs font-semibold text-white shadow-sm
                       bg-emerald-600 hover:bg-emerald-700 active:scale-95"
          >
            Agregar al carrito
          </button>
        </div>
      </div>
    </article>
  );
}
