// Pantalla para rutas que no existen.
import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <>
      <h1>Página no encontrada</h1>
      <p>
        La dirección no existe. <Link to="/agencia/clientes">Volver a clientes</Link>
      </p>
    </>
  );
}
