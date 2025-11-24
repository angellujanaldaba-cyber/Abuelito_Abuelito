// src/data/productos.ts

export type CategoriaProducto =
  | "Bodas"
  | "Cumpleaños"
  | "Infantiles"
  | "Clásicos";

export interface Producto {
  id: number;
  nombre: string;
  descripcion: string;
  precio: number;
  categoria: CategoriaProducto;
  imagenUrl: string;
}

export const productos: Producto[] = [
  {
    id: 1,
    nombre: "Pastel Abuelito de Chocolate",
    descripcion: "Bizcocho húmedo de chocolate con ganache y chispas.",
    precio: 320,
    categoria: "Clásicos",
    imagenUrl: "https://images.pexels.com/photos/291528/pexels-photo-291528.jpeg",
  },
  {
    id: 2,
    nombre: "Pastel de Fresas con Crema",
    descripcion: "Relleno de crema batida y fresas frescas.",
    precio: 380,
    categoria: "Cumpleaños",
    imagenUrl: "https://images.pexels.com/photos/2915285/pexels-photo-2915285.jpeg",
  },
  {
    id: 3,
    nombre: "Pastel Infantil Super Héroe",
    descripcion: "Decorado con temática de super héroes para niños.",
    precio: 450,
    categoria: "Infantiles",
    imagenUrl: "https://images.pexels.com/photos/2915286/pexels-photo-2915286.jpeg",
  },
  {
    id: 4,
    nombre: "Pastel de Boda Clásico",
    descripcion: "Tres pisos, vainilla y relleno de frutos rojos.",
    precio: 1200,
    categoria: "Bodas",
    imagenUrl: "https://images.pexels.com/photos/265801/pexels-photo-265801.jpeg",
  },
  {
    id: 5,
    nombre: "Pastel Tres Leches",
    descripcion: "Clásico tres leches con toque de canela.",
    precio: 340,
    categoria: "Clásicos",
    imagenUrl: "https://images.pexels.com/photos/2915287/pexels-photo-2915287.jpeg",
  },
  {
    id: 6,
    nombre: "Pastel Unicornio",
    descripcion: "Colores pastel, ideal para fiestas infantiles.",
    precio: 420,
    categoria: "Infantiles",
    imagenUrl: "https://images.pexels.com/photos/2915288/pexels-photo-2915288.jpeg",
  },
];
