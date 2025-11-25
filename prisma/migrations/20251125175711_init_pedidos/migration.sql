/*
  Warnings:

  - You are about to alter the column `total` on the `Pedido` table. The data in that column could be lost. The data in that column will be cast from `DoublePrecision` to `Integer`.
  - You are about to drop the column `productoId` on the `PedidoItem` table. All the data in the column will be lost.
  - You are about to alter the column `precio` on the `PedidoItem` table. The data in that column could be lost. The data in that column will be cast from `DoublePrecision` to `Integer`.
  - The primary key for the `Producto` table will be changed. If it partially fails, the table could be left without primary key constraint.
  - You are about to drop the column `id` on the `Producto` table. All the data in the column will be lost.
  - You are about to drop the column `imagen` on the `Producto` table. All the data in the column will be lost.
  - You are about to alter the column `precio` on the `Producto` table. The data in that column could be lost. The data in that column will be cast from `DoublePrecision` to `Integer`.
  - Added the required column `nombre` to the `PedidoItem` table without a default value. This is not possible if the table is not empty.

*/
-- DropForeignKey
ALTER TABLE "PedidoItem" DROP CONSTRAINT "PedidoItem_productoId_fkey";

-- AlterTable
ALTER TABLE "Pedido" ALTER COLUMN "total" SET DATA TYPE INTEGER;

-- AlterTable
ALTER TABLE "PedidoItem" DROP COLUMN "productoId",
ADD COLUMN     "imagenurl" TEXT,
ADD COLUMN     "nombre" TEXT NOT NULL,
ALTER COLUMN "precio" SET DATA TYPE INTEGER;

-- AlterTable
ALTER TABLE "Producto" DROP CONSTRAINT "Producto_pkey",
DROP COLUMN "id",
DROP COLUMN "imagen",
ADD COLUMN     "idProducto" SERIAL NOT NULL,
ADD COLUMN     "imgproducto" TEXT,
ALTER COLUMN "precio" SET DATA TYPE INTEGER,
ADD CONSTRAINT "Producto_pkey" PRIMARY KEY ("idProducto");
