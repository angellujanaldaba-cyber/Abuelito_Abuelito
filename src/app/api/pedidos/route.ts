import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function POST(req: Request) {
  try {
    const data = await req.json();

    const { nombre, telefono, direccion, comentarios, carrito, total } = data;

    if (!nombre || !telefono || !direccion || !carrito || carrito.length === 0) {
      return NextResponse.json(
        { error: "Datos incompletos" },
        { status: 400 }
      );
    }

    const pedido = await prisma.pedido.create({
      data: {
        nombre,
        telefono,
        direccion,
        comentarios,
        total,
        items: {
          create: carrito.map((item: any) => ({
            nombre: item.nombre,
            precio: Number(item.precio),
            cantidad: Number(item.cantidad),
            imagenurl: item.imagenurl ?? null,
          })),
        },
      },
      include: {
        items: true,
      },
    });

    return NextResponse.json(
        { id: pedido.id },
        { status: 201 }
      );
        } catch (error) {
    console.error("Error creando pedido", error);
    return NextResponse.json(
      { error: "Error creando pedido" },
      { status: 500 }
    );
  }
}
