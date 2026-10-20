import Row from "react-bootstrap/Row";
import Col from "react-bootstrap/Col";

import MovieCard from "./MovieCard";

function SkeletonGrid() {
  return (
    <Row className="g-4">
      {[0, 1, 2, 3].map((i) => (
        <Col xs={6} md={4} lg={3} key={i}>
          <div className="ca-skeleton" />
        </Col>
      ))}
    </Row>
  );
}

export default function MovieGrid({ movies, loading, error, onOpen }) {
  if (loading) return <SkeletonGrid />;

  if (error) {
    return <div className="ca-empty">No se pudo cargar la cartelera: {error}</div>;
  }

  if (!movies?.length) {
    return <div className="ca-empty">Todavía no hay películas en cartelera.</div>;
  }

  return (
    <Row className="g-4">
      {movies.map((movie) => (
        <Col xs={6} md={4} lg={3} key={movie.id}>
          <MovieCard movie={movie} onOpen={onOpen} />
        </Col>
      ))}
    </Row>
  );
}
