"use client"

import { useEffect, useState } from "react"

type Event = {
  id: string
  status: string
  evidenceUrl: string | null
  detectedAt: string
}

export default function RetailGuardPage() {
  const [events, setEvents] = useState<Event[]>([])

  useEffect(() => {
    fetch("/api/retailguard/events")
      .then(res => {
        if (!res.ok) {
          throw new Error("Error fetching events")
        }
        return res.json()
      })
      .then(data => setEvents(data))
      .catch(error => console.error(error))
  }, [])

  return (
    <div style={{ padding: 20 }}>
      <h1>RetailGuard AI</h1>

      {events.map(e => (
        <div
          key={e.id}
          style={{
            border: "1px solid #ccc",
            marginBottom: 20,
            padding: 10
          }}
        >
          <p>
            <strong>Status:</strong>{" "}
            <span
              style={{
                color: e.status === "ALERT" ? "red" : "green",
                fontWeight: "bold"
              }}
            >
              {e.status}
            </span>
          </p>

          <p>{new Date(e.detectedAt).toLocaleString()}</p>

          {e.evidenceUrl ? (
            <img
              src={`/${e.evidenceUrl}`}
              alt="evidence"
              style={{
                width: 300,
                borderRadius: 8,
                border: "1px solid #ddd"
              }}
            />
          ) : (
            <p style={{ color: "#777" }}>Sin evidencia visual</p>
          )}
        </div>
      ))}
    </div>
  )
}