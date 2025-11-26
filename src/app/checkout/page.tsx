"use client";

import { useState, FormEvent } from "react";
import { useCarrito } from "@/store/carrito";
import { useRouter } from "next/navigation";

export default function CheckoutPage() {
  // estado del formulario
  const [form, setForm] = useState({
    nombre: "",
    telefono: "",
    direccion: "",
    comentarios: "",
  });

  const [mensaje, setMensaje] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [enviando] = useState(false);

  const carrito = useCarrito((state) => state.items);
  const total = carrito.reduce(
    (acc, item) => acc + item.precio * item.cantidad,
    0
  );

  const router = useRouter();

  // ==============================
  //      HANDLE SUBMIT
  // ==============================
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setMensaje(null);
    setError(null);

    try {
      const res = await fetch("/api/pedidos", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...form,
          total,
          carrito,
        }),
      });

      // si API responde con error
      if (!res.ok) {
        throw new Error("No se pudo crear el pedido");
      }

      // si API responde bien → obtener ID
      const pedidoCreado = await res.json();

      console.log("Pedido guardado:", pedidoCreado);

      // redirigir a pedido-exito
      router.push(`/pedido-exito?id=${pedidoCreado.id}`);
      return;
    } catch (err) {
      console.error(err);
      setError("Ocurrió un error al guardar tu pedido.");
    }
  };

  // ==============================
  //       RENDER DEL COMPONENTE
  // ==============================
  return (
    <main className="min-h-screen p-10">
      <h1 className="text-4xl font-bold mb-6">Finalizar pedido</h1>

      <form onSubmit={handleSubmit} className="max-w-xl space-y-4">
        <input
          className="w-full border p-2 rounded"
          placeholder="Nombre completo"
          value={form.nombre}
          onChange={(e) =>
            setForm({ ...form, nombre: e.target.value })
          }
        />

        <input
          className="w-full border p-2 rounded"
          placeholder="Teléfono"
          value={form.telefono}
          onChange={(e) =>
            setForm({ ...form, telefono: e.target.value })
          }
        />

        <input
          className="w-full border p-2 rounded"
          placeholder="Dirección"
          value={form.direccion}
          onChange={(e) =>
            setForm({ ...form, direccion: e.target.value })
          }
        />

        <textarea
          className="w-full border p-2 rounded"
          placeholder="Comentarios"
          value={form.comentarios}
          onChange={(e) =>
            setForm({ ...form, comentarios: e.target.value })
          }
        />

        {error && (
          <p className="p-3 bg-red-200 text-red-800 rounded">{error}</p>
        )}

        <button
          type="submit"
          disabled={enviando}
          className="bg-emerald-600 text-white px-4 py-2 rounded"
        >
          Confirmar pedido
        </button>
      </form>
    </main>
  );
}
