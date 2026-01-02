# Guía de Reportería - AuditBrain API

Esta guía describe cómo consumir los endpoints de reportería para construir dashboards efectivos.

## Endpoints Disponibles

### 1. Resumen General de Auditorías

**Endpoint:** `GET /api/reports/audits/summary/`

**Autenticación:** Bearer Token requerido

**Descripción:** Obtiene un resumen general con totales y distribución por estado.

**Respuesta:**

```json
{
  "total": 120,
  "active": 115,
  "deleted": 5,
  "by_status": {
    "pending": 30,
    "in_progress": 50,
    "completed": 40,
    "planned": 5
  }
}
```

**Uso en Dashboard:**

- Tarjetas de KPIs (total, activas, completadas)
- Gráfico de dona/pie para distribución por estado
- Indicadores de progreso

---

### 2. Auditorías por Período

**Endpoint:** `GET /api/reports/audits/by-period/`

**Autenticación:** Bearer Token requerido

**Query Parameters:**

- `start_date` (opcional): Fecha de inicio en formato ISO (ej: `2025-01-01T00:00:00Z`)
- `end_date` (opcional): Fecha de fin en formato ISO
- `grouping` (opcional): Tipo de agrupación - `daily`, `weekly`, `monthly` (default: `monthly`)

**Ejemplo de Request:**

```
GET /api/reports/audits/by-period/?start_date=2025-01-01T00:00:00Z&end_date=2025-12-31T23:59:59Z&grouping=monthly
```

**Respuesta:**

```json
{
  "labels": ["2025-01", "2025-02", "2025-03"],
  "data": [12, 20, 18],
  "grouping": "monthly"
}
```

**Uso en Dashboard:**

- Gráfico de líneas para tendencias
- Gráfico de barras para comparación mensual
- Los arrays `labels` y `data` están listos para Chart.js, Recharts, etc.

**Ejemplo con Chart.js:**

```javascript
const response = await fetch(
  "/api/reports/audits/by-period/?grouping=monthly",
  {
    headers: { Authorization: `Bearer ${token}` },
  }
);
const reportData = await response.json();

new Chart(ctx, {
  type: "line",
  data: {
    labels: reportData.labels,
    datasets: [
      {
        label: "Auditorías por Mes",
        data: reportData.data,
      },
    ],
  },
});
```

---

### 3. Productividad por Auditor

**Endpoint:** `GET /api/reports/audits/by-user/`

**Autenticación:** Bearer Token requerido

**Descripción:** Muestra la productividad de cada auditor (auditorías creadas y completadas).

**Respuesta:**

```json
[
  {
    "user_id": "uuid-123",
    "user_name": "Juan Pérez",
    "user_email": "juan@example.com",
    "created": 15,
    "completed": 10
  },
  {
    "user_id": "uuid-456",
    "user_name": "María García",
    "user_email": "maria@example.com",
    "created": 12,
    "completed": 8
  }
]
```

**Uso en Dashboard:**

- Tabla de productividad por usuario
- Gráfico de barras comparativo
- Ranking de auditores
- Cálculo de tasa de completitud: `(completed / created) * 100`

---

### 4. Eventos por Auditoría

**Endpoint:** `GET /api/reports/events/by-audit/`

**Autenticación:** Bearer Token requerido

**Descripción:** Resumen de eventos de calendario asociados a auditorías.

**Respuesta:**

```json
{
  "total_events": 45,
  "upcoming_events": 12,
  "by_audit": [
    {
      "audit_id": "uuid-789",
      "audit_title": "Auditoría Q1 2025",
      "event_count": 5
    }
  ]
}
```

**Uso en Dashboard:**

- KPI de eventos totales y próximos
- Lista de auditorías con más eventos
- Alertas de eventos próximos

---

### 5. Resumen de Evidencias

**Endpoint:** `GET /api/reports/evidences/summary/`

**Autenticación:** Bearer Token requerido

**Descripción:** Resumen de evidencias subidas, agrupadas por tipo y auditoría.

**Respuesta:**

```json
{
  "total_evidences": 230,
  "by_type": {
    "pdf": 120,
    "jpg": 50,
    "docx": 40,
    "xlsx": 20
  },
  "by_audit": [
    {
      "audit_id": "uuid-789",
      "audit_title": "Auditoría Q1 2025",
      "evidence_count": 15
    }
  ]
}
```

**Uso en Dashboard:**

- KPI de evidencias totales
- Gráfico de distribución por tipo de archivo
- Lista de auditorías con más evidencias

---

## Consideraciones de Performance

### Caching

Los endpoints de reportería son ideales para caching:

```javascript
// Ejemplo con React Query
const { data } = useQuery(
  ["audit-summary"],
  fetchAuditSummary,
  { staleTime: 5 * 60 * 1000 } // Cache por 5 minutos
);
```

### Polling vs Refresh Manual

- Para dashboards en tiempo real: polling cada 30-60 segundos
- Para reportes estáticos: refresh manual o al cargar la página

### Manejo de Errores

```javascript
try {
  const response = await fetch("/api/reports/audits/summary/", {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!response.ok) {
    if (response.status === 401) {
      // Token expirado, redirigir a login
    }
    throw new Error("Error al cargar reporte");
  }

  const data = await response.json();
  // Usar datos...
} catch (error) {
  console.error("Error:", error);
  // Mostrar mensaje de error al usuario
}
```

---

## Logging de Consultas

Todas las consultas de reportería se registran automáticamente en MongoDB con:

- Tipo de reporte ejecutado
- Filtros aplicados
- Tiempo de ejecución
- Usuario que ejecutó la consulta

Esto permite analizar patrones de uso del dashboard.

---

## Mejores Prácticas

1. **Usar filtros de fecha**: Para reportes grandes, siempre especificar rango de fechas
2. **Agrupar apropiadamente**: Usar `daily` para períodos cortos, `monthly` para períodos largos
3. **Implementar loading states**: Los reportes pueden tardar algunos milisegundos
4. **Manejar datos vacíos**: Validar que los arrays no estén vacíos antes de renderizar gráficos
5. **Formatear fechas**: Las fechas vienen en formato ISO, formatear según locale del usuario

---

## Ejemplo Completo de Dashboard

```javascript
import React, { useEffect, useState } from "react";
import { Line, Pie } from "react-chartjs-2";

function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [byPeriod, setByPeriod] = useState(null);
  const token = localStorage.getItem("access_token");

  useEffect(() => {
    // Cargar resumen
    fetch("/api/reports/audits/summary/", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => res.json())
      .then(setSummary);

    // Cargar tendencia
    fetch("/api/reports/audits/by-period/?grouping=monthly", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => res.json())
      .then(setByPeriod);
  }, []);

  if (!summary || !byPeriod) return <div>Cargando...</div>;

  return (
    <div>
      <h1>Dashboard de Auditorías</h1>

      {/* KPIs */}
      <div className="kpis">
        <div className="kpi">
          <h3>Total</h3>
          <p>{summary.total}</p>
        </div>
        <div className="kpi">
          <h3>Activas</h3>
          <p>{summary.active}</p>
        </div>
        <div className="kpi">
          <h3>Completadas</h3>
          <p>{summary.by_status.completed}</p>
        </div>
      </div>

      {/* Gráfico de tendencia */}
      <div className="chart">
        <h2>Tendencia Mensual</h2>
        <Line
          data={{
            labels: byPeriod.labels,
            datasets: [
              {
                label: "Auditorías",
                data: byPeriod.data,
                borderColor: "rgb(75, 192, 192)",
                tension: 0.1,
              },
            ],
          }}
        />
      </div>

      {/* Gráfico de distribución */}
      <div className="chart">
        <h2>Distribución por Estado</h2>
        <Pie
          data={{
            labels: Object.keys(summary.by_status),
            datasets: [
              {
                data: Object.values(summary.by_status),
                backgroundColor: [
                  "rgb(255, 205, 86)",
                  "rgb(54, 162, 235)",
                  "rgb(75, 192, 192)",
                ],
              },
            ],
          }}
        />
      </div>
    </div>
  );
}

export default Dashboard;
```

---

## Soporte

Para más información sobre los endpoints de reportería, consulta:

- Colección de Postman: `docs/AuditBrain.postman_collection.json`
- Colección de Insomnia: `docs/AuditBrain.insomnia.json`
- Documentación de la API: README.md
