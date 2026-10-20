import { Link } from "react-router-dom";
import Container from "react-bootstrap/Container";
import Row from "react-bootstrap/Row";
import Col from "react-bootstrap/Col";

export default function Footer() {
  return (
    <footer className="ca-footer">
      <Container>
        <Row className="g-4">
          <Col md={5} lg={4}>
            <Link to="/" className="ca-logo">
              <span className="ca-logo-mark">🎬</span>
              <span className="ca-logo-text">
                CINE<span>ARCADE</span>
              </span>
            </Link>
            <p className="ca-footer-text">
              La cartelera que se vive como un arcade. Compra tus entradas online, elige sala y hora, y
              entra directo a la función.
            </p>
          </Col>

          <Col xs={6} md={3} lg={3}>
            <h4 className="ca-footer-title">Explora</h4>
            <Link className="ca-footer-link" to="/">
              Cartelera
            </Link>
            <Link className="ca-footer-link" to="/funciones">
              Funciones
            </Link>
            <Link className="ca-footer-link" to="/mis-entradas">
              Mis entradas
            </Link>
          </Col>

          <Col xs={6} md={4} lg={5}>
            <h4 className="ca-footer-title">Visítanos</h4>
            <p className="ca-footer-text">
              Calle Jardín de la Isla, 6
              <br />
              Bellavista · Sevilla
            </p>
            <p className="ca-footer-text">
              Mié a Vie: 17:00 — 21:00
              <br />
              Sáb, Dom y Festivos: 11:00 — 21:00
            </p>
          </Col>
        </Row>

        <div className="ca-footer-bottom">
          <span>© 2026 Cine Arcade. Todos los derechos reservados.</span>
          <span className="ca-badge-neon">FREE PLAY · SIN COLAS</span>
        </div>
      </Container>
    </footer>
  );
}
