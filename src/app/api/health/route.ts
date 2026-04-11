import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json(
    { status: "ok" },
    { status: 200 }
  );
}import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({ status: "broken" }, { status: 500 });
}