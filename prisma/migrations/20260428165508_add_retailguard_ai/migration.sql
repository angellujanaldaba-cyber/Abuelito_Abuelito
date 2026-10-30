/*
  Warnings:

  - You are about to drop the column `usuarioId` on the `Pedido` table. All the data in the column will be lost.
  - You are about to alter the column `total` on the `Pedido` table. The data in that column could be lost. The data in that column will be cast from `DoublePrecision` to `Integer`.
  - You are about to drop the `Usuario` table. If the table is not empty, all the data it contains will be lost.

*/
-- CreateEnum
CREATE TYPE "RetailDocumentType" AS ENUM ('SALE', 'RETURN', 'TRANSFER', 'WASTE', 'OWNER_WITHDRAWAL', 'SUPPLIER_RETURN', 'INVENTORY_ADJUSTMENT');

-- CreateEnum
CREATE TYPE "RetailEventStatus" AS ENUM ('OK', 'ALERT');

-- CreateEnum
CREATE TYPE "RetailAlertSeverity" AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');

-- DropForeignKey
ALTER TABLE "Pedido" DROP CONSTRAINT "Pedido_usuarioId_fkey";

-- AlterTable
ALTER TABLE "Pedido" DROP COLUMN "usuarioId",
ALTER COLUMN "total" SET DATA TYPE INTEGER;

-- DropTable
DROP TABLE "Usuario";

-- CreateTable
CREATE TABLE "retail_documents" (
    "id" TEXT NOT NULL,
    "type" "RetailDocumentType" NOT NULL,
    "reference" TEXT,
    "amount" DOUBLE PRECISION,
    "notes" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "retail_documents_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "exit_events" (
    "id" TEXT NOT NULL,
    "eventType" TEXT NOT NULL,
    "cameraId" TEXT NOT NULL,
    "detectedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "evidenceUrl" TEXT,
    "status" "RetailEventStatus" NOT NULL,
    "matchedDocumentId" TEXT,

    CONSTRAINT "exit_events_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "retail_alerts" (
    "id" TEXT NOT NULL,
    "eventId" TEXT NOT NULL,
    "severity" "RetailAlertSeverity" NOT NULL,
    "message" TEXT NOT NULL,
    "sentAt" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "retail_alerts_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "retail_documents_createdAt_idx" ON "retail_documents"("createdAt");

-- CreateIndex
CREATE INDEX "exit_events_detectedAt_idx" ON "exit_events"("detectedAt");

-- CreateIndex
CREATE INDEX "exit_events_status_idx" ON "exit_events"("status");

-- CreateIndex
CREATE INDEX "retail_alerts_createdAt_idx" ON "retail_alerts"("createdAt");

-- AddForeignKey
ALTER TABLE "exit_events" ADD CONSTRAINT "exit_events_matchedDocumentId_fkey" FOREIGN KEY ("matchedDocumentId") REFERENCES "retail_documents"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "retail_alerts" ADD CONSTRAINT "retail_alerts_eventId_fkey" FOREIGN KEY ("eventId") REFERENCES "exit_events"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
