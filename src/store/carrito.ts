// src/store/carrito.ts
"use client";

import { create } from "zustand";
import type { Producto } from "@/data/productos";

export interface ItemCarrito extends Producto {
  cantidad: number;
}

interface EstadoCarrito {
  items: ItemCarrito[];
  agregar: (producto: Producto) => void;
  vaciar: () => void;
}

export const useCarrito = create<EstadoCarrito>((set, get) => ({
  items: [],

  agregar: (producto) => {
    const items = get().items;
    const existe = items.find((p) => p.id === producto.id);

    if (existe) {
      set({
        items: items.map((p) =>
          p.id === producto.id ? { ...p, cantidad: p.cantidad + 1 } : p
        ),
      });
    } else {
      set({
        items: [...items, { ...producto, cantidad: 1 }],
      });
    }
  },

  vaciar: () => set({ items: [] }),
}));
