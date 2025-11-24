// src/store/carrito.ts
"use client";

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { Producto } from "@/data/productos";

export interface ItemCarrito extends Producto {
  cantidad: number;
}

interface EstadoCarrito {
  items: ItemCarrito[];
  agregar: (producto: Producto) => void;
  vaciar: () => void;
  incrementar: (id: number) => void;
  reducir: (id: number) => void;
  eliminar: (id: number) => void;
}

export const useCarrito = create<EstadoCarrito>()(
  persist(
    (set, get) => ({
      items: [],

      agregar: (producto) => {
        const items = get().items;
        const existe = items.find((p) => p.id === producto.id);

        if (existe) {
          set({
            items: items.map((p) =>
              p.id === producto.id
                ? { ...p, cantidad: p.cantidad + 1 }
                : p
            ),
          });
        } else {
          set({
            items: [...items, { ...producto, cantidad: 1 }],
          });
        }
      },

      incrementar: (id) => {
        const items = get().items.map((p) =>
          p.id === id ? { ...p, cantidad: p.cantidad + 1 } : p
        );
        set({ items });
      },

      reducir: (id) => {
        const items = get().items
          .map((p) =>
            p.id === id ? { ...p, cantidad: p.cantidad - 1 } : p
          )
          .filter((p) => p.cantidad > 0); // si llega a 0, se quita
        set({ items });
      },

      eliminar: (id) => {
        const items = get().items.filter((p) => p.id !== id);
        set({ items });
      },

      vaciar: () => set({ items: [] }),
    }),
    {
      name: "carrito-storage",
      storage: createJSONStorage(() => localStorage),
    }
  )
);
