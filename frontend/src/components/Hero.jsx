import { Link } from "react-router-dom";
import Container from "react-bootstrap/Container";

export default function Hero({ movies = "—", showtimes = "—" }) {
  return (
    <section className="ca-hero">
      <div className="ca-hero-grid" aria-hidden="true" />
      <Container className="ca-hero-inner">
        <p className="ca-eyebrow">◆ CARTELERA EN VIVO ◆</p>
        <h1 className="ca-hero-title">
          Vive el cine
          <br />
          <span className="ca-grad">como un arcade</span>
        </h1>
        <p className="ca-hero-sub">
          Cartelera, funciones y compra de entradas online. Elige tu película, tu sala y tu hora — sin
          colas, sin monedas, todo free play.
        </p>
        <div className="ca-hero-actions">
          <Link className="ca-btn ca-btn-primary ca-btn-lg" to="/funciones">
            COMPRAR ENTRADAS
          </Link>
          <button
            type="button"
            className="ca-btn ca-btn-outline ca-btn-lg"
            onClick={() =>
              document.getElementById("cartelera")?.scrollIntoView({ behavior: "smooth", block: "start" })
            }
          >
            VER CARTELERA
          </button>
        </div>

        <div className="ca-stats">
          <div className="ca-stat">
            <b>{movies}</b>
            <span>Películas</span>
          </div>
          <div className="ca-stat">
            <b>{showtimes}</b>
            <span>Funciones</span>
          </div>
          <div className="ca-stat">
            <b>4.8★</b>
            <span>Valoración</span>
          </div>
          <div className="ca-stat">
            <b>100%</b>
            <span>Online</span>
          </div>
        </div>
      </Container>
    </section>
  );
}
