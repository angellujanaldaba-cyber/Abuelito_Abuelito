export async function GET() {
    return Response.json({
      version: process.env.NEXT_PUBLIC_VERSION || "unknown",
    });
  }