"use client";

import { useState, FormEvent } from "react";
import Link from "next/link";
import { useCarrito } from "@/store/carrito";

type CheckoutForm = {
  nombre: string;
  telefono: string;
  direccion: string;
  comentarios: string;
};

export default function CheckoutPage() {
  // 🛒 Leemos el carrito desde Zustand
  const carrito = useCarrito((state: any) => state.items ?? state.productos ?? []);
  // Si más adelante quieres vaciar el carrito desde aquí:
  // const vaciarCarrito = useCarrito((state: any) => state.vaciarCarrito);

  const [form, setForm] = useState<CheckoutForm>({
    nombre: "",
    telefono: "",
    direccion: "",
    comentarios: "",
  });

  const [enviando, setEnviando] = useState(false);
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const total = carrito.reduce((acc: number, item: any) => {
    const precio = Number(item.precio) || 0;
    const cantidad = Number(item.cantidad) || 1;
    return acc + precio * cantidad;
  }, 0);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setEnviando(true);
    setMensaje(null);
    setError(null);

    try {
        console.log("🛒 Carrito a enviar (completo):");
        carrito.forEach((item, index) => {
          console.log(`Producto ${index + 1}:`, JSON.stringify(item, null, 2));
        });
        
      console.log("🧾 Datos del form:", form);
      console.log("💰 Total:", total);
      
      const res = await fetch("/api/pedidos", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...form,
          total,
          carrito,
        }),
      });

      if (!res.ok) {
        throw new Error("No se pudo crear el pedido");
      }

      const data = await res.json();
      console.log("✅ Pedido guardado en BD:", data);

      setMensaje("Tu pedido ha sido generado correctamente, aparte de guapo eres una maquina de guerra ✅");
      // Si quieres, aquí luego:
      // vaciarCarrito();
      // router.push("/gracias");
    } catch (err) {
      console.error(err);
      setError("Ocurrió un error al guardar tu pedido. Intenta de nuevo.");
    } finally {
      setEnviando(false);
    }
  };

  // Si no hay nada en el carrito
  if (!carrito || carrito.length === 0) {
    return (
      <main className="min-h-screen bg-slate-50">
        <div className="max-w-2xl mx-auto px-4 py-16 text-center">
          <h1 className="text-3xl font-bold mb-4">Tu carrito está vacío</h1>
          <p className="text-slate-600 mb-8">
            Primero agrega algunos pastelitos al carrito para poder hacer tu pedido.
          </p>
          <Link
            href="/catalogo"
            className="inline-flex items-center justify-center rounded-full px-6 py-3 text-sm font-semibold bg-pink-500 text-white hover:bg-pink-600 transition"
          >
            Ir al catálogo
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-50">
      <div className="max-w-5xl mx-auto px-4 py-10 lg:py-16">
        {/* Migas de pan */}
        <nav className="text-sm mb-6 text-slate-500">
          <ul className="flex flex-wrap items-center gap-1">
            <li>
              <Link href="/" className="hover:text-pink-600 transition">
                Inicio
              </Link>
            </li>
            <li>/</li>
            <li>
              <Link href="/catalogo" className="hover:text-pink-600 transition">
                Catálogo
              </Link>
            </li>
            <li>/</li>
            <li>
              <Link href="/carrito" className="hover:text-pink-600 transition">
                Carrito
              </Link>
            </li>
            <li>/</li>
            <li className="font-medium text-slate-700">Checkout</li>
          </ul>
        </nav>

        {/* Encabezado */}
        <div className="flex flex-col gap-4 mb-8 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="text-3xl lg:text-4xl font-bold text-slate-900">
              Finalizar pedido
            </h1>
            <p className="text-slate-600 mt-2">
              Revisa tu pedido y completa tus datos para confirmar la entrega 🧁
            </p>
          </div>
          <div className="text-right">
            <p className="text-xs uppercase tracking-wide text-slate-500">
              Total a pagar
            </p>
            <p className="text-2xl font-bold text-pink-600">
              ${total.toFixed(2)}
            </p>
          </div>
        </div>

        {/* Layout 2 columnas */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Formulario */}
          <section className="lg:col-span-2">
            <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 lg:p-8">
              <h2 className="text-xl font-semibold text-slate-900 mb-4">
                Datos de entrega
              </h2>
              <p className="text-sm text-slate-500 mb-6">
                Usa un número y dirección donde podamos confirmar y entregar tu pedido.
              </p>

              <form onSubmit={handleSubmit} className="space-y-5">
                <div className="space-y-1.5">
                  <label
                    htmlFor="nombre"
                    className="block text-sm font-medium text-slate-700"
                  >
                    Nombre completo
                  </label>
                  <input
                    id="nombre"
                    name="nombre"
                    type="text"
                    required
                    value={form.nombre}
                    onChange={handleChange}
                    className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-pink-500 focus:ring-2 focus:ring-pink-100"
                    placeholder="Ej. Miguel Hernández"
                  />
                </div>

                <div className="space-y-1.5">
                  <label
                    htmlFor="telefono"
                    className="block text-sm font-medium text-slate-700"
                  >
                    Teléfono de contacto
                  </label>
                  <input
                    id="telefono"
                    name="telefono"
                    type="tel"
                    required
                    value={form.telefono}
                    onChange={handleChange}
                    className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-pink-500 focus:ring-2 focus:ring-pink-100"
                    placeholder="Ej. 55 1234 5678"
                  />
                </div>

                <div className="space-y-1.5">
                  <label
                    htmlFor="direccion"
                    className="block text-sm font-medium text-slate-700"
                  >
                    Dirección de entrega
                  </label>
                  <textarea
                    id="direccion"
                    name="direccion"
                    required
                    value={form.direccion}
                    onChange={handleChange}
                    className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-pink-500 focus:ring-2 focus:ring-pink-100 min-h-[80px]"
                    placeholder="Calle, número, colonia, referencia cercana..."
                  />
                </div>

                <div className="space-y-1.5">
                  <label
                    htmlFor="comentarios"
                    className="block text-sm font-medium text-slate-700"
                  >
                    Comentarios / instrucciones especiales (opcional)
                  </label>
                  <textarea
                    id="comentarios"
                    name="comentarios"
                    value={form.comentarios}
                    onChange={handleChange}
                    className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-pink-500 focus:ring-2 focus:ring-pink-100 min-h-[80px]"
                    placeholder="Ej. Entregar antes de las 4 pm, pastel para 10 personas..."
                  />
                </div>

                {mensaje && (
                  <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800">
                    {mensaje}
                  </div>
                )}

                {error && (
                  <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
                    {error}
                  </div>
                )}

                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between pt-2">
                  <Link
                    href="/carrito"
                    className="text-sm text-slate-500 hover:text-slate-700 underline-offset-4 hover:underline"
                  >
                    ← Volver al carrito
                  </Link>

                  <button
                    type="submit"
                    disabled={enviando}
                    className="inline-flex items-center justify-center rounded-full px-6 py-3 text-sm font-semibold bg-pink-500 text-white hover:bg-pink-600 disabled:opacity-60 disabled:cursor-not-allowed transition"
                  >
                    {enviando ? "Procesando pedido..." : "Confirmar pedido"}
                  </button>
                </div>
              </form>
            </div>
          </section>

          {/* Resumen del pedido */}
          <aside className="lg:col-span-1">
            <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 space-y-4">
              <h2 className="text-lg font-semibold text-slate-900">
                Resumen del pedido
              </h2>

              <div className="space-y-3 max-h-72 overflow-y-auto pr-1">
                {carrito.map((item: any) => (
                  <div
                    key={item.id ?? item.nombre}
                    className="flex items-start gap-3 border-b border-slate-100 pb-3 last:border-0 last:pb-0"
                  >
                    {item.imagen && (
                      <div className="w-12 h-12 rounded-xl bg-slate-100 overflow-hidden flex-shrink-0" />
                    )}
                    <div className="flex-1">
                      <p className="text-sm font-medium text-slate-900">
                        {item.nombre}
                      </p>
                      <p className="text-xs text-slate-500">
                        Cantidad: {item.cantidad ?? 1}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-semibold text-slate-900">
                        ${Number(item.precio).toFixed(2)}
                      </p>
                      <p className="text-xs text-slate-500">
                        Subtotal: $
                        {(
                          (Number(item.precio) || 0) * (item.cantidad ?? 1)
                        ).toFixed(2)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>

              <div className="border-t border-dashed border-slate-200 pt-4 space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-500">Subtotal</span>
                  <span className="font-medium text-slate-800">
                    ${total.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Envío</span>
                  <span className="font-medium text-slate-800">
                    A convenir
                  </span>
                </div>
                <div className="flex justify-between pt-2 border-t border-slate-100">
                  <span className="text-sm font-semibold text-slate-900">
                    Total
                  </span>
                  <span className="text-lg font-bold text-pink-600">
                    ${total.toFixed(2)}
                  </span>
                </div>
              </div>

              <p className="text-xs text-slate-500 pt-1">
                Este checkout ya envía tus datos a la API y los guarda en PostgreSQL
                usando Prisma. Puedes ver los pedidos en las tablas <strong>Pedido</strong> y{" "}
                <strong>PedidoItem</strong> desde pgAdmin.
              </p>
            </div>
          </aside>
        </div>
      </div>
    </main>
  );
}
