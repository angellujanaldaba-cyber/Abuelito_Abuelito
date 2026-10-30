import { NextResponse } from "next/server"
import { prisma } from "@/lib/prisma"
import { SNSClient, PublishCommand } from "@aws-sdk/client-sns"

const sns = new SNSClient({
  region: process.env.AWS_REGION || "us-east-1"
})

export async function GET() {
  try {
    const events = await prisma.exitEvent.findMany({
      orderBy: { detectedAt: "desc" },
      take: 50,
      include: {
        matchedDocument: true,
        alerts: true
      }
    })

    return NextResponse.json(events)
  } catch (error) {
    console.error(error)
    return NextResponse.json(
      { error: "Error fetching events" },
      { status: 500 }
    )
  }
}

export async function POST(req: Request) {
  try {
    const body = await req.json()
    const { eventType, cameraId, evidenceUrl } = body

    const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000)

    const document = await prisma.retailDocument.findFirst({
      where: {
        createdAt: {
          gte: fiveMinutesAgo
        }
      },
      orderBy: {
        createdAt: "desc"
      }
    })

    let status: "OK" | "ALERT" = "OK"
    let riskMessage = "Salida válida con documento"

    if (!document) {
      status = "ALERT"
      riskMessage = "Salida de producto sin documento"
    }

    const event = await prisma.exitEvent.create({
      data: {
        eventType,
        cameraId,
        evidenceUrl,
        status,
        matchedDocumentId: document?.id || null
      }
    })

    if (status === "ALERT") {
      const alert = await prisma.retailAlert.create({
        data: {
          eventId: event.id,
          severity: "HIGH",
          message: riskMessage
        }
      })

      if (process.env.SNS_TOPIC_ARN) {
        console.log("Publicando alerta en SNS:", process.env.SNS_TOPIC_ARN)

        await sns.send(
          new PublishCommand({
            TopicArn: process.env.SNS_TOPIC_ARN,
            Message: JSON.stringify({
              type: "RETAILGUARD_ALERT",
              eventId: event.id,
              alertId: alert.id,
              eventType,
              cameraId,
              evidenceUrl,
              status,
              message: riskMessage,
              detectedAt: event.detectedAt
            })
          })
        )

        console.log("Alerta publicada en SNS correctamente")
      } else {
        console.log("SNS_TOPIC_ARN no está configurado")
      }
    }

    return NextResponse.json({
      event,
      documentFound: !!document,
      message: riskMessage
    })
  } catch (error) {
    console.error("Error processing event:", error)
    return NextResponse.json(
      { error: "Error processing event" },
      { status: 500 }
    )
  }
}