import { NextResponse } from "next/server"
import { prisma } from "@/lib/prisma"

export async function POST(req: Request) {
  try {
    const body = await req.json()

    const document = await prisma.retailDocument.create({
      data: {
        type: body.type,
        reference: body.reference,
        amount: body.amount,
        notes: body.notes
      }
    })

    return NextResponse.json(document)
  } catch (error) {
    console.error(error)
    return NextResponse.json(
      { error: "Error creating document" },
      { status: 500 }
    )
  }
}