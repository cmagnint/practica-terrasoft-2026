import { getHealth } from "@/lib/api";

//pagina principal del sistema
export default async function Home() {

  try {

    const health = await getHealth();

    return (
      <main className="p-8">
        <h1 className="text-3xl font-bold mb-6">
          Huerto Santa Elena
        </h1>

        <div className="space-y-2">
          <p>Estado API: {health.status}</p>
          <p>Version: {health.version}</p>
          <p>Supervisores: {health.supervisores}</p>
          <p>Trabajadores: {health.trabajadores}</p>
          <p>Cuarteles: {health.cuarteles}</p>
          <p>Registros: {health.registros}</p>
        </div>
      </main>
    );
  }

  catch (error) {

    return (
      <main className="p-8">
        <h1 className="text-3xl font-bold mb-6">
          Huerto Santa Elena
        </h1>

        <p>
          No fue posible conectar con el backend.
        </p>
      </main>
    );
  }
}