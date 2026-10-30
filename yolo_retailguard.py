from ultralytics import YOLO
import cv2
import requests
import os
from datetime import datetime

# 🔗 API
API_URL = "http://localhost:3000/api/retailguard/events"

# 🤖 Modelo
model = YOLO("yolov8n.pt")

# 📷 Cámara (0 = webcam / DroidCam / Iriun)
cap = cv2.VideoCapture(0)

# 📏 Línea de salida
line_y = 300

# 🧠 IDs ya procesados
tracked_ids = set()

# 📁 Carpeta para evidencia
os.makedirs("public/evidence", exist_ok=True)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # 🔍 Tracking
    results = model.track(frame, persist=True)

    for r in results:
        if r.boxes.id is None:
            continue

        for box, track_id, cls in zip(r.boxes.xyxy, r.boxes.id, r.boxes.cls):
            label = model.names[int(cls)]

            # 👤 SOLO PERSONAS
            if label != "person":
                continue

            x1, y1, x2, y2 = map(int, box)
            track_id = int(track_id)

            center_y = int((y1 + y2) / 2)

            # 🟩 Dibujar caja
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                frame,
                f"{label} ID {track_id}",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2
            )

            # 🚨 Detectar cruce
            if center_y > line_y and track_id not in tracked_ids:
                print(f"🚨 CRUCE DETECTADO ID {track_id}")

                try:
                    # 🕒 Timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                    # 📁 Ruta REAL (donde se guarda)
                    evidence_path = f"public/evidence/event_{track_id}_{timestamp}.jpg"

                    # 🌐 Ruta para frontend (SIN public/)
                    evidence_url = f"evidence/event_{track_id}_{timestamp}.jpg"

                    # 💾 Guardar imagen
                    cv2.imwrite(evidence_path, frame)

                    # 📡 Enviar evento
                    response = requests.post(API_URL, json={
                        "eventType": "EXIT_WITH_PRODUCT",
                        "cameraId": "camara-01",
                        "evidenceUrl": evidence_url
                    })

                    print("Respuesta:", response.json())

                except Exception as e:
                    print("Error:", e)

                tracked_ids.add(track_id)

    # 🔴 Dibujar línea
    cv2.line(frame, (0, line_y), (frame.shape[1], line_y), (0, 0, 255), 2)

    # 🖥️ Mostrar video
    cv2.imshow("RetailGuard AI", frame)

    # ❌ Salir con Q
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# 🔚 Liberar recursos
cap.release()
cv2.destroyAllWindows()