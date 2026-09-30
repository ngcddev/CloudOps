// Aviso visible cuando la consola muestra datos de prueba porque la API no responde.
import { useEffect, useState } from "react";

import { isUsingMockData } from "../api";

export default function MockDataNotice() {
  const [usingMock, setUsingMock] = useState(false);

  useEffect(() => {
    isUsingMockData().then(setUsingMock);
  }, []);

  if (!usingMock) return null;
  return (
    <p className="notice" role="status">
      <strong>ⓘ Datos de prueba.</strong> La API no responde; se muestran los datos de <code>seed/</code> y
      los registros nuevos se pierden al recargar la página.
    </p>
  );
}
