export const MESES = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"];

const pad = (n) => String(n).padStart(2, "0");

export function fmtDate(iso) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) {
    return { day: "--", month: "---", time: "--:--", full: String(iso ?? "") };
  }
  return {
    day: pad(d.getDate()),
    month: MESES[d.getMonth()],
    time: `${pad(d.getHours())}:${pad(d.getMinutes())}`,
    full: d.toLocaleString("es-ES", {
      day: "2-digit",
      month: "long",
      hour: "2-digit",
      minute: "2-digit",
    }),
  };
}

export function genreEmoji(genre = "") {
  const g = String(genre).toLowerCase();
  if (g.includes("ciencia")) return "🚀";
  if (g.includes("acción") || g.includes("accion")) return "💥";
  if (g.includes("animación") || g.includes("animacion")) return "🎨";
  if (g.includes("crimen")) return "🔫";
  if (g.includes("aventura")) return "🗺️";
  if (g.includes("romance")) return "💘";
  if (g.includes("musical")) return "🎵";
  if (g.includes("terror")) return "👻";
  if (g.includes("drama")) return "🎭";
  return "🎬";
}

export function posterStyle(movie) {
  const hue = ((movie?.id || 0) * 47) % 360;
  return {
    backgroundImage: `linear-gradient(160deg, hsl(${hue} 70% 24%), hsl(${(hue + 50) % 360} 82% 9%))`,
  };
}

export function price(value) {
  return `${Number(value || 0).toFixed(2)} €`;
}

/** Etiquetas legibles de los roles de usuario. */
export const ROLE_LABELS = {
  user: "Cliente",
  manager: "Jefe",
  admin: "Informático",
};

export function roleLabel(role) {
  return ROLE_LABELS[role] || role || "";
}
