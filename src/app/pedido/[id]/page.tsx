import { prisma } from "@/lib/prisma";
import { notFound } from "next/navigation";

// ⚠️ Server Component — NO usar "use client"

export default async function PedidoDetallePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  // ⬇️ FIX: Next.js 15/16 entrega params como PROMESA
  const { id } = await params;
  const numericId = Number(id);

  if (isNaN(numericId)) return notFound();

  // Buscar pedido con items
  const pedido = await prisma.pedido.findUnique({
    where: { id: numericId },
    include: {
      items: true,
    },
  });

  if (!pedido) return notFound();

  return (
    <main className="max-w-3xl mx-auto py-16">
      <h1 className="text-4xl font-bold text-emerald-700 mb-6">
        Pedido #{pedido.id}
      </h1>

      <section className="bg-white p-6 rounded-lg shadow mb-10">
        <h2 className="text-2xl font-bold mb-4">Datos del cliente</h2>
        <p><strong>Nombre:</strong> {pedido.nombre}</p>
        <p><strong>Teléfono:</strong> {pedido.telefono}</p>
        <p><strong>Dirección:</strong> {pedido.direccion}</p>
        {pedido.comentarios && (
          <p><strong>Comentarios:</strong> {pedido.comentarios}</p>
        )}
        <p className="mt-2 text-gray-600">
          <strong>Fecha:</strong>{" "}
          {pedido.createdAt.toLocaleString("es-MX")}
        </p>
      </section>

      <section className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-2xl font-bold mb-4">Artículos comprados</h2>

        {pedido.items.map((item: any) => (
  <div key={item.id} className="border-b py-4">
    <p className="text-lg font-semibold">{item.nombre}</p>
    <p className="text-gray-700">
      Precio: ${item.precio} — Cantidad: {item.cantidad}
    </p>
  </div>
))}


        <h3 className="text-2xl font-bold text-right mt-6">
          Total: ${pedido.total}
        </h3>
      </section>
    </main>
  );
}
