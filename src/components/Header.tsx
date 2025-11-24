"use client";

import Link from "next/link";
import { ShoppingCart } from "lucide-react";
import { useCarrito } from "@/store/carrito";

export function Header() {
  const totalItems = useCarrito((state) =>
    state.items.reduce((acc, item) => acc + item.cantidad, 0)
  );

  return (
    <header className="w-full border-b bg-white px-6 py-4 flex justify-between items-center">
      <Link href="/" className="text-xl font-bold text-slate-900">
        Pastelería Abuelito
      </Link>

      <Link href="/carrito" className="flex items-center gap-2 text-slate-700">
        <ShoppingCart />

        <span>Carrito</span>

        {totalItems > 0 && (
          <span className="bg-emerald-600 text-white px-2 py-0.5 rounded-full text-xs">
            {totalItems}
          </span>
        )}
      </Link>
    </header>
  );
}
