# 🎬 MovieLens 1M Dashboard — Hito 1 (v2.1.0-beta)

Taller de Visualización de la Información · UDD 2026-2
Vicente Sánchez · Matilda Rodríguez

Dashboard en **Streamlit + Plotly** sobre MovieLens 1M (1.000.209 calificaciones de 6.040 usuarios a 3.706 películas).

## Qué incluye (requisitos del Hito 1)

- **Filtros globales (4):** género de la película, sexo, rango de edad y año de estreno.
- **KPIs (4):** calificaciones, rating promedio (con delta vs global), usuarios activos y películas calificadas.
- **Gráficos Plotly (5):** distribución de ratings, promedio por género, promedio por año de estreno, segmentación edad × sexo y mapa de usuarios por región ZIP.
- **Primer mapa / segmentación:** mapa coroplético de EE.UU. por primer dígito del ZIP y barras por segmento de edad y sexo.
- Top 10 películas con mínimo de calificaciones ajustable y tabla de datos filtrados.
- Cada gráfico trae una interpretación que se recalcula con los filtros.

## Ejecutar

```bash
pip install -r requirements.txt
streamlit run tips_app.py
```

Los archivos `ratings.dat`, `users.dat` y `movies.dat` van en la carpeta `data/`. Si no están en el repositorio, la app pide subirlos desde el panel lateral.

Archivo principal en Streamlit Community Cloud: `tips_app.py`.

## Versión

```bash
git tag -a v2.1.0-beta -m "Hito 1: filtros, KPIs, gráficos y primer mapa"
git push origin v2.1.0-beta
```

## Plan hacia el Hito 2 (v3.0.0)

| Tarea | Responsable |
|---|---|
| Mapa por estado más preciso (ZIP de 3 dígitos) | Vicente |
| Página de recomendaciones / similitud entre películas | Matilda |
| Pestañas por análisis (st.tabs) y estilo final | Vicente |
| Interpretaciones finales y presentación | Matilda |
