// Atrapa los errores de render de una pantalla para que no se desmonte toda la aplicación y quede en blanco (auditoría FE-04).
import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // Queda en la consola del navegador para quien lo reporte; no se envía a ningún servicio externo
    console.error("Error al mostrar la pantalla:", error, info.componentStack);
  }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div className="error" role="alert">
        <p>
          <strong>⚠ Algo salió mal al mostrar esta pantalla.</strong>
        </p>
        <p className="muted">Puedes reintentar o volver al inicio. Si sigue pasando, avisa al equipo.</p>
        <div className="button-row">
          <button type="button" className="button" onClick={() => this.setState({ error: null })}>
            Reintentar
          </button>
          <a href="/">Ir al inicio</a>
        </div>
      </div>
    );
  }
}
