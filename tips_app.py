# app.py
# ============================================================
#  DASHBOARD MOVIELENS 1M — Hito 1 (v2.1.0-beta)
#  Taller de Visualización de la Información · UDD 2026-2
#  Vicente Sánchez · Matilda Rodríguez
#
#  Ejecutar:  streamlit run app.py
#
#  Datos: carpeta data/ con los archivos originales de MovieLens 1M
#  (ratings.dat, users.dat, movies.dat; separador "::").
# ============================================================

import io
import os
import re

import pandas as pd
import plotly.express as px
import streamlit as st

# ── 1. CONFIGURACIÓN DE LA PÁGINA ────────────────────────────
st.set_page_config(
    page_title="MovieLens Dashboard",
    page_icon="🎬",
    layout="wide",
)

# ── 2. DICCIONARIOS Y ESTILO COMPARTIDO ──────────────────────
# Códigos de edad y ocupación según la documentación de MovieLens 1M.
EDADES = {1: "Menor de 18", 18: "18-24", 25: "25-34", 35: "35-44",
          45: "45-49", 50: "50-55", 56: "56+"}
ORDEN_EDADES = list(EDADES.values())

OCUPACIONES = {
    0: "Otra", 1: "Académico/educador", 2: "Artista", 3: "Administrativo",
    4: "Estudiante universitario", 5: "Atención al cliente", 6: "Salud",
    7: "Ejecutivo/gerente", 8: "Agricultor", 9: "Dueño(a) de casa",
    10: "Estudiante escolar", 11: "Abogado", 12: "Programador",
    13: "Jubilado", 14: "Ventas/marketing", 15: "Científico",
    16: "Independiente", 17: "Técnico/ingeniero", 18: "Oficios",
    19: "Desempleado", 20: "Escritor",
}

SEXOS = {"F": "Mujer", "M": "Hombre"}
COLOR_SEXO = {"Mujer": "#7F77DD", "Hombre": "#378ADD"}

# Primer dígito del código ZIP de EE.UU. → estados que cubre.
# Sirve para ubicar a los usuarios en un mapa sin geocodificar.
REGIONES_ZIP = {
    "0": ["CT", "MA", "ME", "NH", "NJ", "RI", "VT"],
    "1": ["DE", "NY", "PA"],
    "2": ["DC", "MD", "NC", "SC", "VA", "WV"],
    "3": ["AL", "FL", "GA", "MS", "TN"],
    "4": ["IN", "KY", "MI", "OH"],
    "5": ["IA", "MN", "MT", "ND", "SD", "WI"],
    "6": ["IL", "KS", "MO", "NE"],
    "7": ["AR", "LA", "OK", "TX"],
    "8": ["AZ", "CO", "ID", "NM", "NV", "UT", "WY"],
    "9": ["AK", "CA", "HI", "OR", "WA"],
}

LAYOUT = dict(
    plot_bgcolor="white", paper_bgcolor="white",
    font=dict(family="Inter,Arial,sans-serif", size=12),
    margin=dict(t=50, b=40, l=50, r=20),
)


# ── 3. CARGAR Y PREPARAR LOS DATOS ───────────────────────────
# Los archivos se leen desde data/ si están en el repositorio. Si no
# están, la app pide subirlos (como en la app de regresión de clase).
# @st.cache_data: el millón de calificaciones se procesa una sola vez.
ARCHIVOS = ["ratings.dat", "users.dat", "movies.dat"]


def leer_dat(fuente, columnas, **extra):
    return pd.read_csv(fuente, sep="::", engine="python", names=columnas,
                       encoding="latin-1", **extra)


@st.cache_data
def cargar_datos(ratings_b, users_b, movies_b):
    ratings = leer_dat(io.BytesIO(ratings_b), ["UserID", "MovieID", "Rating", "Timestamp"])
    users = leer_dat(io.BytesIO(users_b), ["UserID", "Gender", "Age", "Occupation", "Zip"],
                     dtype={"Zip": str})
    movies = leer_dat(io.BytesIO(movies_b), ["MovieID", "Title", "Genres"])

    # Limpieza: año de estreno desde el título y nombres en español
    movies["Año"] = movies["Title"].str.extract(r"\((\d{4})\)\s*$").astype(float)
    users["Sexo"] = users["Gender"].map(SEXOS)
    users["Edad"] = users["Age"].map(EDADES)
    users["Ocupación"] = users["Occupation"].map(OCUPACIONES)
    users["Región ZIP"] = users["Zip"].str[0]

    df = ratings.merge(users, on="UserID").merge(movies, on="MovieID")
    df["Fecha"] = pd.to_datetime(df["Timestamp"], unit="s")
    return df, movies


if all(os.path.exists(os.path.join("data", a)) for a in ARCHIVOS):
    contenidos = [open(os.path.join("data", a), "rb").read() for a in ARCHIVOS]
else:
    st.sidebar.header("Datos MovieLens 1M")
    subidos = [st.sidebar.file_uploader(f"Sube {a}", type=["dat"], key=a) for a in ARCHIVOS]
    if not all(subidos):
        st.title("¿Qué y cómo califican los usuarios de MovieLens?")
        st.info("Sube los 3 archivos de MovieLens 1M (ratings.dat, users.dat y "
                "movies.dat) en el panel lateral para comenzar.")
        st.stop()
    contenidos = [f.getvalue() for f in subidos]

df, movies = cargar_datos(*contenidos)
GENEROS = sorted({g for gs in movies["Genres"] for g in gs.split("|")})

# ── 4. SIDEBAR — FILTROS GLOBALES ────────────────────────────
with st.sidebar:
    st.title("🎬 MovieLens 1M")
    st.caption("Filtros globales — afectan todos los gráficos")

    generos = st.multiselect("Género de la película", options=GENEROS,
                             default=[], placeholder="Todos los géneros")

    sexo = st.radio("Sexo del usuario", options=["Todos", "Mujer", "Hombre"])

    edades = st.multiselect("Rango de edad", options=ORDEN_EDADES,
                            default=ORDEN_EDADES)

    año_min, año_max = int(df["Año"].min()), int(df["Año"].max())
    años = st.slider("Año de estreno", min_value=año_min, max_value=año_max,
                     value=(año_min, año_max))

    st.divider()
    st.caption(f"Dataset completo: {len(df):,} calificaciones")

# ── 5. APLICAR LOS FILTROS (pandas puro) ─────────────────────
mask = df["Edad"].isin(edades) & df["Año"].between(*años)
if sexo != "Todos":
    mask &= df["Sexo"] == sexo
if generos:
    patron = "|".join(re.escape(g) for g in generos)
    mask &= df["Genres"].str.contains(patron, regex=True)

dff = df[mask]

# ── 6. ENCABEZADO ─────────────────────────────────────────────
st.title("¿Qué y cómo califican los usuarios de MovieLens?")
st.caption(f"Mostrando {len(dff):,} de {len(df):,} calificaciones con los filtros aplicados")

if dff.empty:
    st.warning("No hay datos para los filtros seleccionados. Ajusta el panel lateral.")
    st.stop()

# ── 7. KPIs ───────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
prom = dff["Rating"].mean()
prom_global = df["Rating"].mean()

k1.metric("Calificaciones", f"{len(dff):,}")
k2.metric("Rating promedio", f"{prom:.2f} / 5",
          delta=f"{prom - prom_global:+.2f} vs global")
k3.metric("Usuarios activos", f"{dff['UserID'].nunique():,}")
k4.metric("Películas calificadas", f"{dff['MovieID'].nunique():,}")

st.divider()

# ── 8. FILA 1 — DISTRIBUCIÓN Y GÉNEROS ───────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("Distribución de las calificaciones")
    conteo = dff["Rating"].value_counts().sort_index().reset_index()
    conteo.columns = ["Rating", "Cantidad"]
    fig = px.bar(conteo, x="Rating", y="Cantidad", color="Rating",
                 color_continuous_scale="Blues",
                 title="Cantidad de calificaciones por estrella")
    fig.update_layout(**LAYOUT, coloraxis_showscale=False)
    st.plotly_chart(fig, width="stretch")
    pct = conteo.set_index("Rating")["Cantidad"] / conteo["Cantidad"].sum() * 100
    st.caption(f"Interpretación: las notas 3 y 4 suman {pct.get(3, 0) + pct.get(4, 0):.0f}% "
               f"de las calificaciones, mientras que 1 estrella es solo {pct.get(1, 0):.0f}%.")

with col2:
    st.subheader("Rating promedio por género")
    g = dff[["Genres", "Rating"]].assign(Género=dff["Genres"].str.split("|")).explode("Género")
    if generos:
        g = g[g["Género"].isin(generos)]
    por_genero = (g.groupby("Género")["Rating"].agg(["mean", "count"])
                    .reset_index().rename(columns={"mean": "Promedio", "count": "Calificaciones"})
                    .sort_values("Promedio"))
    fig = px.bar(por_genero, x="Promedio", y="Género", orientation="h",
                 color="Calificaciones", color_continuous_scale="Viridis",
                 hover_data={"Calificaciones": ":,"},
                 title="Promedio de estrellas (color = volumen)")
    fig.update_layout(**LAYOUT, xaxis_range=[1, 5])
    st.plotly_chart(fig, width="stretch")
    mejor = por_genero.iloc[-1]
    masivo = por_genero.sort_values("Calificaciones").iloc[-1]
    st.caption(f"Interpretación: {mejor['Género']} tiene el mejor promedio "
               f"({mejor['Promedio']:.2f}), mientras que {masivo['Género']} es el género "
               f"con más calificaciones ({int(masivo['Calificaciones']):,}).")

# ── 9. FILA 2 — EVOLUCIÓN Y SEGMENTACIÓN ─────────────────────
col3, col4 = st.columns(2)

with col3:
    st.subheader("Rating promedio según año de estreno")
    por_año = (dff.groupby("Año")["Rating"].agg(["mean", "count"]).reset_index()
                 .rename(columns={"mean": "Promedio", "count": "Calificaciones"}))
    por_año = por_año[por_año["Calificaciones"] >= 20]  # evita años con muy pocos datos
    fig = px.line(por_año, x="Año", y="Promedio", markers=True,
                  hover_data={"Calificaciones": ":,"},
                  title="Promedio por año (años con 20+ calificaciones)")
    fig.update_layout(**LAYOUT)
    st.plotly_chart(fig, width="stretch")
    if len(por_año) > 2:
        tendencia = por_año["Año"].corr(por_año["Promedio"])
        texto = ("las películas más antiguas obtienen mejores notas (sesgo de clásicos)"
                 if tendencia < 0 else "las películas más recientes obtienen mejores notas")
        st.caption(f"Interpretación: {texto}; correlación año-promedio = {tendencia:.2f}.")

with col4:
    st.subheader("Segmentación de usuarios: edad y sexo")
    seg = (dff.groupby(["Edad", "Sexo"])["Rating"].mean().reset_index()
              .rename(columns={"Rating": "Promedio"}))
    fig = px.bar(seg, x="Edad", y="Promedio", color="Sexo", barmode="group",
                 color_discrete_map=COLOR_SEXO,
                 category_orders={"Edad": ORDEN_EDADES},
                 title="Rating promedio por segmento")
    fig.update_layout(**LAYOUT, yaxis_range=[1, 5], legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig, width="stretch")
    por_edad = dff.groupby("Edad")["Rating"].mean().reindex(ORDEN_EDADES).dropna()
    if len(por_edad) > 1:
        st.caption(f"Interpretación: el segmento {por_edad.index[0]} promedia "
                   f"{por_edad.iloc[0]:.2f} y el segmento {por_edad.index[-1]} promedia "
                   f"{por_edad.iloc[-1]:.2f}; así se compara cómo califica cada grupo.")

# ── 10. FILA 3 — MAPA DE USUARIOS ─────────────────────────────
st.subheader("¿Dónde están los usuarios? (primer mapa)")
usuarios = dff.drop_duplicates("UserID")
por_region = usuarios["Región ZIP"].value_counts().reset_index()
por_region.columns = ["Región ZIP", "Usuarios"]
filas = [{"Estado": e, "Región ZIP": r, "Usuarios": n}
         for r, n in zip(por_region["Región ZIP"], por_region["Usuarios"])
         for e in REGIONES_ZIP.get(r, [])]
mapa = pd.DataFrame(filas)
if not mapa.empty:
    fig = px.choropleth(mapa, locations="Estado", locationmode="USA-states",
                        color="Usuarios", scope="usa",
                        hover_data={"Región ZIP": True, "Usuarios": ":,"},
                        color_continuous_scale="Blues",
                        title="Usuarios por región del código ZIP")
    fig.update_layout(**LAYOUT)
    st.plotly_chart(fig, width="stretch")
    top_r = por_region.iloc[0]
    st.caption(f"Interpretación: cada región agrupa los estados que comparten el primer "
               f"dígito del ZIP. La región {top_r['Región ZIP']} "
               f"({', '.join(REGIONES_ZIP.get(top_r['Región ZIP'], []))}) concentra más "
               f"usuarios: {int(top_r['Usuarios']):,}.")

# ── 11. TOP PELÍCULAS ─────────────────────────────────────────
st.subheader("Top 10 películas mejor calificadas")
minimo = st.slider("Mínimo de calificaciones por película", 10, 500, 100, step=10,
                   key="min_ratings")
top = (dff.groupby("Title")["Rating"].agg(["mean", "count"]).reset_index()
          .rename(columns={"Title": "Película", "mean": "Promedio", "count": "Calificaciones"}))
top = top[top["Calificaciones"] >= minimo].sort_values("Promedio", ascending=False).head(10)
st.dataframe(top.round({"Promedio": 2}), width="stretch", hide_index=True)

with st.expander("Ver datos filtrados (primeras 1.000 filas)"):
    cols = ["Title", "Genres", "Año", "Rating", "Sexo", "Edad", "Ocupación", "Fecha"]
    st.dataframe(dff[cols].head(1000), width="stretch", hide_index=True)
