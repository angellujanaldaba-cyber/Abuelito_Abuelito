"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useCarrito } from "@/store/carrito";

export default function PedidoExitoPage() {
  const params = useSearchParams();
  const id = params.get("id");
  const vaciar = useCarrito((state) => state.vaciar);

  // vaciar carrito al entrar a esta página
  if (typeof window !== "undefined") {
    vaciar();
  }

  return (
    <main className="min-h-screen flex flex-col justify-center items-center p-10">
      <h1 className="text-4xl font-bold text-emerald-600 mb-4">
        ¡Pedido realizado con éxito! 🎉
      </h1>

      <p className="text-lg mb-6">
        Tu pedido se registró correctamente.
      </p>

      {id && (
        <p className="text-xl font-semibold mb-6">
          Número de pedido: <span className="text-emerald-700">{id}</span>
        </p>
      )}

      <Link
        href="/"
        className="px-6 py-3 bg-emerald-600 text-white rounded-full text-lg"
      >
        Volver al inicio
      </Link>
    </main>
  );
}
