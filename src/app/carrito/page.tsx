// src/app/carrito/page.tsx
"use client";

import { useCarrito } from "@/store/carrito";

export default function CarritoPage() {
  const { items, vaciar, incrementar, reducir, eliminar } = useCarrito();

  const total = items.reduce(
    (suma, item) => suma + item.precio * item.cantidad,
    0
  );

  return (
    <main className="min-h-screen px-6 py-10">
      <h1 className="text-3xl font-bold mb-6">Carrito</h1>

      {items.length === 0 && (
        <p className="text-lg text-slate-500">Tu carrito está vacío.</p>
      )}

      {items.length > 0 && (
        <>
          <ul className="space-y-4">
            {items.map((item) => (
              <li
                key={item.id}
                className="flex justify-between items-center border rounded-lg p-4"
              >
                <div>
                  <p className="font-semibold">{item.nombre}</p>

                  {/* Controles de cantidad */}
                  <div className="flex items-center gap-3 mt-2">
                    <button
                      onClick={() => reducir(item.id)}
                      className="px-3 py-1 bg-red-600 text-white rounded-full"
                    >
                      -
                    </button>

                    <span className="font-semibold">{item.cantidad}</span>

                    <button
                      onClick={() => incrementar(item.id)}
                      className="px-3 py-1 bg-emerald-600 text-white rounded-full"
                    >
                      +
                    </button>

                    {/* 🔥 Botón eliminar separado */}
                    <button
                      onClick={() => eliminar(item.id)}
                      className="ml-4 px-3 py-1 bg-slate-300 text-slate-800 rounded-full text-xs hover:bg-slate-400"
                    >
                      Eliminar
                    </button>
                  </div>
                </div>

                <p className="font-bold text-emerald-700">
                  ${(item.precio * item.cantidad).toLocaleString("es-MX")}
                </p>
              </li>
            ))}
          </ul>

          <div className="mt-6 flex justify-between items-center">
            <p className="text-xl font-bold">
              Total: ${total.toLocaleString("es-MX")}
            </p>
            <button
              onClick={vaciar}
              className="rounded-full bg-red-600 text-white px-4 py-2 text-sm font-semibold hover:bg-red-700 active:scale-95"
            >
              Vaciar carrito
            </button>
          </div>
        </>
      )}
    </main>
  );
}
