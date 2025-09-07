import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  const body = await req.json();
  const adkUrl = process.env.NEXT_PUBLIC_ADK_URL || "http://localhost:8080";
  
  // Forward incoming Authorization header if present; otherwise use a dev token fallback.
  const incomingAuth = req.headers.get("authorization") ?? undefined;
  // Support migration: prefer server-only DEV_BEARER; fall back to NEXT_PUBLIC_DEV_BEARER in dev if present.
  const devToken =
    process.env.DEV_BEARER ||
    (process.env.NODE_ENV !== "production" ? process.env.NEXT_PUBLIC_DEV_BEARER : undefined);

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    ...(incomingAuth
      ? { Authorization: incomingAuth }
      : devToken
      ? { Authorization: devToken }
      : {}),
  };

  const r = await fetch(`${adkUrl}/v1/runs/plan`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
  
  const data = await r.json();
  return NextResponse.json(data, { status: r.status });
}