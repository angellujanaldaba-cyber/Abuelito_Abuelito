"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";

export default function PedidoExitoPage() {
  const searchParams = useSearchParams();
  const id = searchParams.get("id");

  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-10">
      <h1 className="text-4xl font-bold text-emerald-700 mb-4">
        ¡Pedido realizado con éxito! 🎉
      </h1>

      <p className="text-lg text-gray-700 mb-6">
        Tu pedido se registró correctamente.
      </p>

      {id && (
        <p className="text-2xl font-bold mb-10">
          Número de pedido: <span className="text-emerald-700">{id}</span>
        </p>
      )}

      <div className="flex gap-4">

        {/* Ver pedido */}
        {id && (
          <Link
            href={`/pedido/${id}`}
            className="bg-emerald-600 text-white px-6 py-3 rounded-full font-semibold hover:bg-emerald-700 transition"
          >
            Ver pedido
          </Link>
        )}

        {/* Volver al inicio */}
        <Link
          href="/"
          className="bg-gray-200 text-gray-700 px-6 py-3 rounded-full font-semibold hover:bg-gray-300 transition"
        >
          Volver al inicio
        </Link>
      </div>
    </main>
  );
}
