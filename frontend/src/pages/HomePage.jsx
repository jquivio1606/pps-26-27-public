import { useEffect, useState } from "react";
import Container from "react-bootstrap/Container";

import { api } from "../api/client";
import Hero from "../components/Hero";
import SectionHeader from "../components/SectionHeader";
import MovieGrid from "../components/MovieGrid";
import PaginationBar from "../components/PaginationBar";
import { useUI } from "../context/UIContext";

const PAGE_SIZE = 8;

export default function HomePage() {
  const { openMovie } = useUI();
  const [page, setPage] = useState(1);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showtimeTotal, setShowtimeTotal] = useState("—");

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    api(`/movies?page=${page}&size=${PAGE_SIZE}`)
      .then((d) => active && setData(d))
      .catch((err) => active && setError(err.message))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [page]);

  useEffect(() => {
    let active = true;
    api("/showtimes?page=1&size=1")
      .then((d) => active && setShowtimeTotal(d.total))
      .catch(() => {});
    return () => {
      active = false;
    };
  }, []);

  return (
    <>
      <Hero movies={data?.total ?? "—"} showtimes={showtimeTotal} />

      <section className="ca-section" id="cartelera">
        <Container>
          <SectionHeader
            eyebrow="EN CARTELERA"
            title="Películas de hoy"
            sub="Pulsa una película para ver sus funciones disponibles."
          />

          <MovieGrid movies={data?.items} loading={loading} error={error} onOpen={openMovie} />

          <PaginationBar
            data={data}
            onChange={(p) => {
              setPage(p);
              document.getElementById("cartelera")?.scrollIntoView({ behavior: "smooth", block: "start" });
            }}
            ariaLabel="Paginación de cartelera"
          />
        </Container>
      </section>
    </>
  );
}
