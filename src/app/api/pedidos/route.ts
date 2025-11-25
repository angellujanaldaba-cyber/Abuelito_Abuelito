import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function POST(request: Request) {
  try {
    const body = await request.json();

    const { nombre, telefono, direccion, comentarios, total, items } = body;

    const pedido = await prisma.pedido.create({
      data: {
        nombre,
        telefono,
        direccion,
        comentarios,
        total,
        items: {
          create: items.map((i: any) => ({
            cantidad: i.cantidad,
            precio: Number(i.precio),
            productoId: i.id,
          })),
        },
      },
      include: { items: true },
    });

    return NextResponse.json({ ok: true, pedido });
  } catch (error) {
    console.error(error);
    return NextResponse.json({ ok: false, error: "Error creando pedido" }, { status: 500 });
  }
}
