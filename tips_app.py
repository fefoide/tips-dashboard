# tips_app.py
# ============================================================
#  DASHBOARD MOVIELENS 1M — Hito 1 (v2.1.0-beta)
#  Taller de Visualización de la Información · UDD 2026-2
#  Vicente Sánchez · Matilda Rodríguez
#  Ejecutar:  streamlit run tips_app.py
# ============================================================

import pandas as pd
import plotly.express as px
import streamlit as st

# ── 1. CONFIGURACIÓN DE LA PÁGINA ────────────────────────────
st.set_page_config(page_title="MovieLens Dashboard", page_icon="🎬", layout="wide")

# ── 2. COLORES Y ORDEN DE CATEGORÍAS ─────────────────────────
COLOR_SEXO = {"Mujer": "#7F77DD", "Hombre": "#378ADD"}
ORDEN_EDADES = ["Menor de 18", "18-24", "25-34", "35-44", "45-49", "50-55", "56+"]


# ── 3. CARGAR Y PREPARAR LOS DATOS ───────────────────────────
# @st.cache_data: el millón de calificaciones se lee una sola vez.
@st.cache_data
def cargar_datos():
    # Los archivos de MovieLens separan columnas con "::"
    ratings = pd.read_csv("data/ratings.dat", sep="::", engine="python",
                          names=["UserID", "MovieID", "Rating", "Timestamp"])
    users = pd.read_csv("data/users.dat", sep="::", engine="python",
                        names=["UserID", "Gender", "Age", "Occupation", "Zip"])
    movies = pd.read_csv("data/movies.dat", sep="::", engine="python",
                         names=["MovieID", "Title", "Genres"], encoding="latin-1")

    # Unir las tres tablas en una sola
    df = ratings.merge(users, on="UserID").merge(movies, on="MovieID")

    # Traducir códigos a texto con .map()
    df["Sexo"] = df["Gender"].map({"F": "Mujer", "M": "Hombre"})
    df["Edad"] = df["Age"].map({1: "Menor de 18", 18: "18-24", 25: "25-34", 35: "35-44",
                                45: "45-49", 50: "50-55", 56: "56+"})

    # El título termina en "(1995)": los caracteres -5 a -1 son el año
    df["Año"] = df["Title"].str[-5:-1].astype(int)

    # Una película puede tener varios géneros ("Action|Comedy"): usamos el primero
    df["Género"] = df["Genres"].str.split("|").str[0]
    return df


df = cargar_datos()

# ── 4. SIDEBAR — FILTROS GLOBALES ────────────────────────────
with st.sidebar:
    st.title("🎬 MovieLens 1M")
    st.caption("Filtros globales — afectan todos los gráficos")

    generos = st.multiselect("Género", options=sorted(df["Género"].unique()),
                             default=sorted(df["Género"].unique()))

    sexo = st.radio("Sexo del usuario", options=["Todos", "Mujer", "Hombre"])

    edades = st.multiselect("Rango de edad", options=ORDEN_EDADES, default=ORDEN_EDADES)

    año_min, año_max = st.slider("Año de estreno",
                                 min_value=int(df["Año"].min()),
                                 max_value=int(df["Año"].max()),
                                 value=(int(df["Año"].min()), int(df["Año"].max())))

# ── 5. APLICAR LOS FILTROS (máscara de pandas) ───────────────
mask = (
    df["Género"].isin(generos) &
    df["Edad"].isin(edades) &
    df["Año"].between(año_min, año_max)
)
if sexo != "Todos":
    mask &= df["Sexo"] == sexo

dff = df[mask]

# ── 6. ENCABEZADO ─────────────────────────────────────────────
st.title("¿Qué y cómo califican los usuarios de MovieLens?")
st.caption(f"Mostrando {len(dff):,} de {len(df):,} calificaciones con los filtros aplicados")

if dff.empty:
    st.warning("No hay datos para los filtros seleccionados. Ajusta el panel lateral.")
    st.stop()

# ── 7. KPIs ───────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
k1.metric("Calificaciones", f"{len(dff):,}")
k2.metric("Rating promedio", f"{dff['Rating'].mean():.2f}",
          delta=f"{dff['Rating'].mean() - df['Rating'].mean():+.2f} vs global")
k3.metric("Usuarios", f"{dff['UserID'].nunique():,}")
k4.metric("Películas", f"{dff['MovieID'].nunique():,}")

st.divider()

# ── 8. FILA 1 — DISTRIBUCIÓN Y GÉNEROS ───────────────────────
col1, col2 = st.columns(2)

with col1:
    conteo = dff["Rating"].value_counts().reset_index()
    fig = px.bar(conteo, x="Rating", y="count",
                 title="Cantidad de calificaciones por estrella")
    st.plotly_chart(fig, width="stretch")
    st.caption("Interpretación: con todos los datos, la nota más común es 4 y las "
               "notas 3 y 4 suman el 61%; solo el 6% pone 1 estrella.")

with col2:
    por_genero = dff.groupby("Género")["Rating"].mean().reset_index()
    por_genero = por_genero.sort_values("Rating")
    fig = px.bar(por_genero, x="Rating", y="Género", orientation="h",
                 title="Rating promedio por género")
    st.plotly_chart(fig, width="stretch")
    st.caption("Interpretación: los géneros de nicho (Film-Noir, documentales) "
               "tienen los promedios más altos.")

# ── 9. FILA 2 — EVOLUCIÓN Y COMPARACIÓN POR EDAD ─────────────
col3, col4 = st.columns(2)

with col3:
    por_año = dff.groupby("Año")["Rating"].mean().reset_index()
    fig = px.line(por_año, x="Año", y="Rating", markers=True,
                  title="Rating promedio según año de estreno")
    st.plotly_chart(fig, width="stretch")
    st.caption("Interpretación: las películas antiguas reciben mejores notas "
               "(sesgo de clásicos).")

with col4:
    por_edad = dff.groupby(["Edad", "Sexo"])["Rating"].mean().reset_index()
    fig = px.bar(por_edad, x="Edad", y="Rating", color="Sexo", barmode="group",
                 color_discrete_map=COLOR_SEXO,
                 category_orders={"Edad": ORDEN_EDADES},
                 title="Rating promedio por edad y sexo")
    st.plotly_chart(fig, width="stretch")
    st.caption("Interpretación: con todos los datos, los mayores de 56 promedian "
               "3,77 y los menores de 18, 3,55.")

# ── 10. SEGMENTACIÓN DE USUARIOS ──────────────────────────────
st.subheader("Segmentación de usuarios")
usuarios = dff.drop_duplicates("UserID")
seg = usuarios.groupby(["Sexo", "Edad"]).size().reset_index(name="usuarios")
fig = px.sunburst(seg, path=["Sexo", "Edad"], values="usuarios",
                  color="Sexo", color_discrete_map=COLOR_SEXO,
                  title="Usuarios por sexo y rango de edad")
st.plotly_chart(fig, width="stretch")
st.caption("Interpretación: el grupo más grande son los hombres de 25 a 34 años (1.538 usuarios).")

# ── 11. TABLA DE DATOS (DESPLEGABLE) ─────────────────────────
with st.expander("Ver datos filtrados"):
    st.dataframe(dff[["Title", "Género", "Año", "Rating", "Sexo", "Edad"]].head(1000),
                 width="stretch", hide_index=True)
