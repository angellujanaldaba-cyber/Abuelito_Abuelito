This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.


## Despliegue EKS y pipelines

La infraestructura vive en [deploy/terraform](deploy/terraform), los manifests en [deploy/kubernetes](deploy/kubernetes) y los registros historicos en [deploy/records](deploy/records).

Leer [docs/deployment/PIPELINES.md](docs/deployment/PIPELINES.md) para configurar GitHub Actions, OIDC, backend remoto y ejecutor privado. Push ejecuta solo compilacion/validacion. El coordinador Deploy complete Abuelito environment prepara plan, aplica tras revision, construye imagenes y ejecuta base/deploy privados con CodeBuild. La implementacion nueva aun no se probo de punta a punta en AWS; consultar [PIPELINE-COMPLETO.md](docs/deployment/PIPELINE-COMPLETO.md). Las pruebas funcionales las realiza el usuario.

El laboratorio AWS del 29 de octubre de 2026 fue destruido. La imagen historica validada esta registrada por digest; este codigo versionado no implica que un build nuevo sea identico a esa imagen. Los respaldos Docker y los datos privados permanecen fuera de Git. El script YOLO es una herramienta local separada; los pesos, entorno Python y evidencias generadas no se versionan aqui ni se ejecutan en los pipelines web.
