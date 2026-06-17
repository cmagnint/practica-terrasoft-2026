const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ??
  "http://localhost:8000/api";

export async function getHealth() {
  const res = await fetch(
    `${API_BASE}/health/`,
    {
      cache: "no-store",
    }
  );

  if (!res.ok) {
    throw new Error(
      `API respondio ${res.status}`
    );
  }

  return res.json();
}