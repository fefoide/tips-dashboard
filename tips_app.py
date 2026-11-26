# tips_app.py
# ============================================================
#  DASHBOARD MOVIELENS 1M — Hito 2 (v3.0.0)
#  Taller de Visualización de la Información · UDD 2026-2
#  Vicente Sánchez · Matilda Rodríguez
#  Ejecutar:  streamlit run tips_app.py
# ============================================================

import json

import pandas as pd
import plotly.express as px
import streamlit as st
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# ── 1. CONFIGURACIÓN DE LA PÁGINA ────────────────────────────
st.set_page_config(page_title="MovieLens · Dashboard", page_icon="🎬", layout="wide")

# ── 2. DISEÑO: PALETA "SALA DE CINE" ─────────────────────────
# Fondo negro (config.toml), dorado de marquesina y rojo de butaca.
DORADO = "#E3B341"
ROJO = "#C0392B"
CREMA = "#F2EDE4"
GRIS = "#8E8A80"
COLOR_SEXO = {"Mujer": DORADO, "Hombre": ROJO}
ESCALA = ["#3A1210", ROJO, DORADO]                  # escala continua oscuro → dorado
COLOR_SEGMENTO = {"Alta exposición": DORADO, "Valoración favorable": "#E67E22",
                  "Menor valoración": ROJO}
ORDEN_SEGMENTOS = ["Alta exposición", "Valoración favorable", "Menor valoración"]

px.defaults.template = "plotly_dark"
px.defaults.color_discrete_sequence = [DORADO, ROJO, GRIS, "#E67E22"]

# CSS: tipografía de marquesina, tarjetas de KPI y pestañas con estilo de cine
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
h1, h2, h3 { font-family: 'Bebas Neue', sans-serif !important; letter-spacing: 1.5px; }
.marquesina {
  border: 2px solid #E3B341; border-radius: 14px; padding: 26px 32px 22px;
  background: linear-gradient(135deg, #1A0F0E 0%, #0E0E12 60%);
  box-shadow: 0 0 0 6px #0E0E12, 0 0 0 7px #3A1210;
  margin-bottom: 18px;
}
.marquesina .cinta { height: 10px; margin: -14px -20px 16px;
  background: repeating-linear-gradient(90deg, #E3B341 0 14px, transparent 14px 26px); opacity: .55; }
.marquesina h1 { color: #E3B341; font-size: 3.1rem; margin: 0; line-height: 1; }
.marquesina p { color: #F2EDE4; opacity: .85; margin: 8px 0 0; font-size: 1.02rem; }
.marquesina .pregunta { color: #E3B341; font-weight: 600; opacity: 1; }
[data-testid="stMetric"] {
  background: #17171E; border: 1px solid #2B2B35; border-left: 4px solid #C0392B;
  border-radius: 10px; padding: 14px 18px;
}
[data-testid="stMetricLabel"] { color: #E3B341 !important; text-transform: uppercase; letter-spacing: 1px; }
.stTabs [data-baseweb="tab-list"] { gap: 6px; border-bottom: 1px solid #2B2B35; }
.stTabs [data-baseweb="tab"] { font-family: 'Bebas Neue', sans-serif; font-size: 1.25rem;
  letter-spacing: 1px; padding: 8px 18px; border-radius: 8px 8px 0 0; }
.stTabs [aria-selected="true"] { background: #1A0F0E; color: #E3B341 !important; }
.hallazgos { background: #17171E; border: 1px solid #2B2B35; border-top: 3px solid #E3B341;
  border-radius: 10px; padding: 16px 22px; }
.hallazgos h3 { color: #E3B341; margin-top: 0; }
[data-testid="stSidebar"] { border-right: 1px solid #3A1210; }
</style>
""", unsafe_allow_html=True)


def estilo(fig):
    """Formato común de todos los gráficos: fondo transparente, fuentes y tooltip."""
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Inter, sans-serif", color=CREMA),
                      title_font=dict(family="Bebas Neue, sans-serif", size=22, color=DORADO),
                      hoverlabel=dict(bgcolor="#1A0F0E", bordercolor=DORADO,
                                      font=dict(color=CREMA)),
                      margin=dict(t=60, l=10, r=10, b=10))
    return fig


ORDEN_EDADES = ["Menor de 18", "18-24", "25-34", "35-44", "45-49", "50-55", "56+"]
OCUPACIONES = {0: "Otra", 1: "Académico/docente", 2: "Artista", 3: "Administrativo",
               4: "Estudiante universitario", 5: "Atención al cliente", 6: "Salud",
               7: "Ejecutivo/gerente", 8: "Agricultor", 9: "Dueño(a) de casa",
               10: "Estudiante escolar", 11: "Abogado", 12: "Programador",
               13: "Jubilado", 14: "Ventas/marketing", 15: "Científico",
               16: "Independiente", 17: "Técnico/ingeniero", 18: "Artesano/oficios",
               19: "Desempleado", 20: "Escritor"}

# Los 3 primeros dígitos del código postal de EE.UU. indican el estado
RANGOS_ZIP = [(10, 27, "Massachusetts"), (28, 29, "Rhode Island"), (30, 38, "New Hampshire"),
              (39, 49, "Maine"), (50, 59, "Vermont"), (60, 69, "Connecticut"),
              (70, 89, "New Jersey"), (100, 149, "New York"), (150, 196, "Pennsylvania"),
              (197, 199, "Delaware"), (200, 205, "District of Columbia"), (206, 219, "Maryland"),
              (220, 246, "Virginia"), (247, 268, "West Virginia"), (270, 289, "North Carolina"),
              (290, 299, "South Carolina"), (300, 319, "Georgia"), (320, 349, "Florida"),
              (350, 369, "Alabama"), (370, 385, "Tennessee"), (386, 397, "Mississippi"),
              (398, 399, "Georgia"), (400, 427, "Kentucky"), (430, 459, "Ohio"),
              (460, 479, "Indiana"), (480, 499, "Michigan"), (500, 528, "Iowa"),
              (530, 549, "Wisconsin"), (550, 567, "Minnesota"), (570, 577, "South Dakota"),
              (580, 588, "North Dakota"), (590, 599, "Montana"), (600, 629, "Illinois"),
              (630, 658, "Missouri"), (660, 679, "Kansas"), (680, 693, "Nebraska"),
              (700, 714, "Louisiana"), (716, 729, "Arkansas"), (730, 749, "Oklahoma"),
              (750, 799, "Texas"), (800, 816, "Colorado"), (820, 831, "Wyoming"),
              (832, 838, "Idaho"), (840, 847, "Utah"), (850, 865, "Arizona"),
              (870, 884, "New Mexico"), (885, 885, "Texas"), (889, 898, "Nevada"),
              (900, 961, "California"), (967, 968, "Hawaii"), (970, 979, "Oregon"),
              (980, 994, "Washington"), (995, 999, "Alaska")]


def zip_a_estado(zip_code):
    prefijo = str(zip_code)[:3]
    if not prefijo.isdigit():
        return None                       # códigos no numéricos (p. ej. Canadá)
    n = int(prefijo)
    for desde, hasta, estado in RANGOS_ZIP:
        if desde <= n <= hasta:
            return estado
    return None


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

    # Traducir códigos a texto con .map()
    users["Sexo"] = users["Gender"].map({"F": "Mujer", "M": "Hombre"})
    users["Edad"] = users["Age"].map({1: "Menor de 18", 18: "18-24", 25: "25-34", 35: "35-44",
                                      45: "45-49", 50: "50-55", 56: "56+"})
    users["Ocupación"] = users["Occupation"].map(OCUPACIONES)
    users["Estado"] = users["Zip"].apply(zip_a_estado)

    # Unir las tres tablas en una sola
    df = ratings.merge(users, on="UserID").merge(movies, on="MovieID")

    # El título termina en "(1995)": los caracteres -5 a -1 son el año
    df["Año"] = df["Title"].str[-5:-1].astype(int)

    # Una película puede tener varios géneros ("Action|Comedy"): usamos el primero
    df["Género"] = df["Genres"].str.split("|").str[0]

    # Timestamp está en segundos: lo pasamos a fecha y nos quedamos con el mes
    df["Mes"] = pd.to_datetime(df["Timestamp"], unit="s").dt.to_period("M").dt.to_timestamp()
    return df


@st.cache_data
def cargar_geojson():
    with open("data/us-states.geojson") as f:
        return json.load(f)


# ── 4. SEGMENTACIÓN DE PELÍCULAS (K-Means, igual que el Certamen 2) ──
@st.cache_data
def segmentar(df):
    # Una fila por película: promedio, cantidad de votos y dispersión (desacuerdo)
    peliculas = df.groupby(["MovieID", "Title", "Género", "Año"])["Rating"].agg(
        promedio="mean", votos="count", dispersion="std").reset_index()

    # Solo películas con 20 votos o más: bajo ese umbral el promedio no es confiable
    peliculas = peliculas[peliculas["votos"] >= 20].copy()
    variables = ["promedio", "votos", "dispersion"]

    # Escalar: (valor - media) / desviación estándar, así "votos" no domina las distancias
    escaladas = (peliculas[variables] - peliculas[variables].mean()) / peliculas[variables].std()

    # k = 3 elegido con el método del codo en el Certamen 2
    modelo = KMeans(n_clusters=3, random_state=2025)
    peliculas["cluster"] = modelo.fit_predict(escaladas)

    # Nombre descriptivo de cada cluster según su perfil
    medias = peliculas.groupby("cluster")[variables].mean()
    c_masivo = medias["votos"].idxmax()            # el de más votos
    c_bajo = medias["promedio"].idxmin()           # el de menor promedio
    c_medio = medias.drop([c_masivo, c_bajo]).index[0]
    nombres = {c_masivo: "Alta exposición", c_medio: "Valoración favorable",
               c_bajo: "Menor valoración"}
    peliculas["Segmento"] = peliculas["cluster"].map(nombres)
    escaladas["Segmento"] = peliculas["Segmento"]
    return peliculas.drop(columns="cluster"), escaladas, variables


df = cargar_datos()
geojson = cargar_geojson()
peliculas, escaladas, VARIABLES = segmentar(df)
df = df.merge(peliculas[["MovieID", "Segmento"]], on="MovieID", how="left")
df["Segmento"] = df["Segmento"].fillna("Sin segmento (< 20 votos)")

# ── 5. SIDEBAR — FILTROS GLOBALES ────────────────────────────
with st.sidebar:
    st.header("Filtros")
    st.caption("Afectan los KPIs y todos los gráficos")

    generos = st.multiselect("Género", options=sorted(df["Género"].unique()),
                             default=sorted(df["Género"].unique()))

    sexo = st.radio("Sexo del usuario", options=["Todos", "Mujer", "Hombre"], horizontal=True)

    edades = st.multiselect("Rango de edad", options=ORDEN_EDADES, default=ORDEN_EDADES)

    año_min, año_max = st.slider("Año de estreno",
                                 min_value=int(df["Año"].min()),
                                 max_value=int(df["Año"].max()),
                                 value=(int(df["Año"].min()), int(df["Año"].max())))

    st.divider()
    st.caption("Datos: MovieLens 1M (GroupLens). 1.000.209 calificaciones de "
               "6.040 usuarios sobre 3.706 películas.")
    st.caption("Vicente Sánchez · Matilda Rodríguez")

# ── 6. APLICAR LOS FILTROS (máscara de pandas) ───────────────
mask = (
    df["Género"].isin(generos) &
    df["Edad"].isin(edades) &
    df["Año"].between(año_min, año_max)
)
if sexo != "Todos":
    mask &= df["Sexo"] == sexo

dff = df[mask]


def miles(n):
    """Formato chileno: 1.000.209"""
    return f"{n:,}".replace(",", ".")


# ── 7. ENCABEZADO Y PREGUNTA DEL DASHBOARD ───────────────────
st.markdown(f"""
<div class="marquesina">
  <div class="cinta"></div>
  <h1>MovieLens 1M · Lo que califica el público</h1>
  <p class="pregunta">Pregunta guía: más allá del promedio, ¿qué películas y géneros valoran
  mejor los usuarios cuando consideramos cuántos votos tienen y cuánto desacuerdo generan?</p>
  <p>Mostrando {miles(len(dff))} de {miles(len(df))} calificaciones con los filtros aplicados.</p>
</div>
""", unsafe_allow_html=True)

if dff.empty:
    st.warning("No hay datos para los filtros seleccionados. Ajusta el panel lateral.")
    st.stop()

# ── 8. KPIs (siempre visibles, sobre las pestañas) ───────────
k1, k2, k3, k4 = st.columns(4)
k1.metric("Calificaciones", miles(len(dff)))
k2.metric("Rating promedio", f"{dff['Rating'].mean():.2f} ★",
          delta=f"{dff['Rating'].mean() - df['Rating'].mean():+.2f} vs total")
k3.metric("Usuarios", miles(dff["UserID"].nunique()))
k4.metric("Películas", miles(dff["MovieID"].nunique()))

st.write("")

# ── 9. PESTAÑAS: un tema por pestaña ─────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Calificaciones", "Películas y géneros", "Usuarios y mapa", "En el tiempo", "Segmentos"])

# ── 9.1 CALIFICACIONES (análisis univariado) ─────────────────
with tab1:
    col1, col2 = st.columns(2)

    with col1:
        conteo = dff["Rating"].value_counts().sort_index().reset_index()
        conteo["Porcentaje"] = conteo["count"] / conteo["count"].sum() * 100
        fig = px.bar(conteo, x="Rating", y="count", hover_name="Rating",
                     hover_data={"Porcentaje": ":.1f", "count": ":,", "Rating": False},
                     labels={"Rating": "Estrellas (1–5)", "count": "Calificaciones (n°)",
                             "Porcentaje": "% del total"},
                     title="Cantidad de calificaciones por estrella")
        st.plotly_chart(estilo(fig), width="stretch")
        st.caption("Con todos los datos, la nota más común es 4 y las notas 3 y 4 suman "
                   "el 61%; solo el 6% pone 1 estrella.")

    with col2:
        # Promedio de cada usuario: ¿hay usuarios "exigentes" y "generosos"?
        prom_usuario = dff.groupby("UserID")["Rating"].mean().reset_index()
        fig = px.histogram(prom_usuario, x="Rating", nbins=30,
                           hover_data={"Rating": ":.2f"},
                           labels={"Rating": "Rating promedio del usuario (1–5)"},
                           title="Distribución del rating promedio de cada usuario")
        fig.update_layout(yaxis_title="Usuarios (n°)")
        st.plotly_chart(estilo(fig), width="stretch")
        st.caption("El 70% de los usuarios promedia entre 3 y 4; solo el 6% es exigente "
                   "(bajo 3) y el 24% es generoso (sobre 4).")

# ── 9.2 PELÍCULAS Y GÉNEROS (relaciones + jerárquico) ────────
with tab2:
    col1, col2 = st.columns(2)

    with col1:
        por_genero = dff.groupby("Género")["Rating"].agg(["mean", "size"]).reset_index()
        por_genero = por_genero.sort_values("mean")
        fig = px.bar(por_genero, x="mean", y="Género", orientation="h", hover_name="Género",
                     hover_data={"mean": ":.2f", "size": ":,", "Género": False},
                     color="mean", color_continuous_scale=ESCALA,
                     labels={"mean": "Rating promedio (1–5)", "size": "Calificaciones (n°)",
                             "Género": ""},
                     title="Rating promedio por género")
        st.plotly_chart(estilo(fig), width="stretch")
        st.caption("Los géneros de nicho (Film-Noir, documentales) tienen los promedios "
                   "más altos; terror es el peor evaluado.")

    with col2:
        # Jerárquico: género → década, el tamaño es la cantidad de calificaciones
        arbol = dff.assign(Década=(dff["Año"] // 10 * 10).astype(str) + "s")
        arbol = arbol.groupby(["Género", "Década"])["Rating"].agg(["size", "mean"]).reset_index()
        fig = px.treemap(arbol, path=[px.Constant("Todas"), "Género", "Década"], values="size",
                         color="mean", color_continuous_scale=ESCALA,
                         hover_data={"size": ":,", "mean": ":.2f"},
                         labels={"size": "Calificaciones (n°)", "mean": "Rating promedio"},
                         title="Calificaciones por género y década de estreno")
        st.plotly_chart(estilo(fig), width="stretch")
        st.caption("Comedia, acción y drama concentran el 74% de las calificaciones, "
                   "sobre todo con películas de los 90.")

    # Relaciones: ¿las películas más vistas son las mejor calificadas?
    por_peli = dff.groupby(["Title", "Género"])["Rating"].agg(["mean", "size"]).reset_index()
    fig = px.scatter(por_peli[por_peli["size"] >= 20], x="size", y="mean", color="Género",
                     hover_name="Title", hover_data={"size": ":,", "mean": ":.2f"},
                     opacity=0.7,
                     labels={"size": "Calificaciones de la película (n°)",
                             "mean": "Rating promedio (1–5)"},
                     title="Popularidad vs. calidad (películas con 20 o más calificaciones)")
    st.plotly_chart(estilo(fig), width="stretch")
    st.caption("Relación positiva (correlación 0,38): las películas con más de 1.000 "
               "calificaciones promedian 3,89, contra 3,10 de las que tienen menos de 100, "
               "cuyas notas además son muy dispersas.")

    # Control local: el slider solo afecta al Top 10
    st.subheader("Top 10 películas mejor calificadas")
    min_votos = st.slider("Mínimo de calificaciones por película (control local)",
                          50, 1000, 300, step=50)
    top10 = por_peli[por_peli["size"] >= min_votos].sort_values("mean").tail(10)
    if top10.empty:
        st.info("Ninguna película cumple el mínimo con estos filtros. Baja el mínimo.")
    else:
        fig = px.bar(top10, x="mean", y="Title", orientation="h", text_auto=".2f",
                     hover_name="Title", hover_data={"size": ":,", "Género": True,
                                                     "Title": False, "mean": ":.2f"},
                     labels={"mean": "Rating promedio (1–5)", "Title": "",
                             "size": "Calificaciones (n°)"},
                     title=f"Top 10 con al menos {min_votos} calificaciones")
        fig.update_traces(marker_color=DORADO)
        st.plotly_chart(estilo(fig), width="stretch")
        st.caption("Con al menos 300 calificaciones lideran clásicos como Seven Samurai, "
                   "Shawshank Redemption y The Godfather, todos sobre 4,5.")

# ── 9.3 USUARIOS Y MAPA (geográfico + jerárquico) ────────────
with tab3:
    usuarios = dff.drop_duplicates("UserID")

    # Geográfico: coropleta por estado con GeoJSON guardado en data/
    st.subheader("¿Dónde están los usuarios?")
    metrica = st.selectbox("Colorear el mapa por (control local)",
                           ["Usuarios", "Rating promedio"])
    por_estado = dff.dropna(subset=["Estado"]).groupby("Estado").agg(
        Usuarios=("UserID", "nunique"), Rating_promedio=("Rating", "mean"),
        Calificaciones=("Rating", "size")).reset_index()
    columna = "Usuarios" if metrica == "Usuarios" else "Rating_promedio"
    fig = px.choropleth_map(por_estado, geojson=geojson, locations="Estado",
                            featureidkey="properties.name", color=columna,
                            color_continuous_scale=ESCALA, hover_name="Estado",
                            hover_data={"Usuarios": ":,", "Rating_promedio": ":.2f",
                                        "Calificaciones": ":,", "Estado": False},
                            labels={"Rating_promedio": "Rating promedio",
                                    "Usuarios": "Usuarios (n°)",
                                    "Calificaciones": "Calificaciones (n°)"},
                            map_style="carto-darkmatter", zoom=3.2,
                            center={"lat": 38.5, "lon": -96.5}, opacity=0.8,
                            title=f"{metrica} por estado de EE.UU.")
    fig.update_layout(height=480)
    st.plotly_chart(estilo(fig), width="stretch")
    sin_estado = df.drop_duplicates("UserID")["Estado"].isna().sum()
    st.caption(f"California concentra la mayor cantidad de usuarios (1.110), seguida por "
               f"Nueva York (468) y Minnesota (433, sede de GroupLens). El estado se obtuvo de los 3 primeros dígitos del código postal; "
               f"{sin_estado} usuarios con códigos no válidos o de fuera de EE.UU. no aparecen "
               f"en el mapa.")

    col1, col2 = st.columns(2)

    with col1:
        seg = usuarios.groupby(["Sexo", "Edad"]).size().reset_index(name="usuarios")
        fig = px.sunburst(seg, path=["Sexo", "Edad"], values="usuarios",
                          color="Sexo", color_discrete_map=COLOR_SEXO,
                          hover_data={"usuarios": ":,"},
                          labels={"usuarios": "Usuarios (n°)"},
                          title="Usuarios por sexo y rango de edad")
        st.plotly_chart(estilo(fig), width="stretch")
        st.caption("El 72% de los usuarios son hombres; el grupo más grande son los "
                   "hombres de 25 a 34 años (1.538 usuarios).")

    with col2:
        por_edad = dff.groupby(["Edad", "Sexo"])["Rating"].agg(["mean", "size"]).reset_index()
        fig = px.bar(por_edad, x="Edad", y="mean", color="Sexo", barmode="group",
                     color_discrete_map=COLOR_SEXO, category_orders={"Edad": ORDEN_EDADES},
                     hover_name="Edad", hover_data={"mean": ":.2f", "size": ":,"},
                     labels={"mean": "Rating promedio (1–5)", "Edad": "Rango de edad",
                             "size": "Calificaciones (n°)"},
                     title="Rating promedio por edad y sexo")
        st.plotly_chart(estilo(fig), width="stretch")
        st.caption("La nota sube con la edad: los mayores de 56 promedian 3,77 y los "
                   "menores de 18, 3,55.")

    col3, col4 = st.columns(2)

    with col3:
        ocup = usuarios["Ocupación"].value_counts().reset_index().sort_values("count")
        fig = px.bar(ocup, x="count", y="Ocupación", orientation="h", hover_name="Ocupación",
                     hover_data={"count": ":,", "Ocupación": False},
                     labels={"count": "Usuarios (n°)", "Ocupación": ""},
                     title="Usuarios por ocupación")
        fig.update_traces(marker_color=ROJO)
        st.plotly_chart(estilo(fig), width="stretch")
        st.caption("Los grupos más grandes son estudiantes universitarios (759), "
                   "'otra' (711) y ejecutivos (679).")

    with col4:
        # Mapa de calor: rating promedio cruzando género y edad
        tabla = dff.pivot_table(index="Género", columns="Edad", values="Rating", aggfunc="mean")
        tabla = tabla[[e for e in ORDEN_EDADES if e in tabla.columns]]
        fig = px.imshow(tabla, text_auto=".1f", aspect="auto", color_continuous_scale=ESCALA,
                        labels={"x": "Rango de edad", "y": "Género", "color": "Rating promedio"},
                        title="Rating promedio por género y edad")
        st.plotly_chart(estilo(fig), width="stretch")
        st.caption("Terror es el peor evaluado en todas las edades (~3,1) y Film-Noir el "
                   "mejor (~4,2).")

# ── 9.4 EN EL TIEMPO (análisis temporal) ─────────────────────
with tab4:
    col1, col2 = st.columns(2)

    with col1:
        por_año = dff.groupby("Año")["Rating"].agg(["mean", "size"]).reset_index()
        fig = px.line(por_año, x="Año", y="mean", markers=True, hover_name="Año",
                      hover_data={"mean": ":.2f", "size": ":,", "Año": False},
                      labels={"mean": "Rating promedio (1–5)", "Año": "Año de estreno",
                              "size": "Calificaciones (n°)"},
                      title="Rating promedio según año de estreno")
        fig.update_traces(line_color=DORADO)
        st.plotly_chart(estilo(fig), width="stretch")
        st.caption("Las películas antiguas reciben mejores notas: es el sesgo de "
                   "clásicos (solo se siguen viendo las buenas).")

    with col2:
        por_mes = dff.groupby("Mes").size().reset_index(name="calificaciones")
        fig = px.area(por_mes, x="Mes", y="calificaciones",
                      hover_data={"calificaciones": ":,", "Mes": "|%B %Y"},
                      labels={"Mes": "Mes de la calificación",
                              "calificaciones": "Calificaciones (n°)"},
                      title="Calificaciones registradas por mes")
        fig.update_traces(line_color=ROJO)
        st.plotly_chart(estilo(fig), width="stretch")
        st.caption("El 90% de las calificaciones se registró en 2000, con un peak en "
                   "noviembre (290 mil); después la actividad cae casi a cero.")

# ── 9.5 SEGMENTOS DE PELÍCULAS (K-Means + radar + perfiles + multidimensional)
with tab5:
    st.caption("Segmentación de películas con K-Means (k = 3), igual que en el Certamen 2: "
               "cada película se describe con su promedio, su cantidad de votos y su "
               "dispersión (desviación estándar de sus estrellas), escaladas a media 0 y "
               "desviación 1. Solo entran películas con 20 votos o más. Elegimos k = 3 por "
               "el método del codo: la inercia baja 37% de k=1 a 2 y 27% de 2 a 3, y desde "
               "k = 4 baja 18,5% o menos; además, k = 3 aísla a las películas masivas.")

    # Solo las películas que quedan con los filtros globales
    p = peliculas[peliculas["MovieID"].isin(dff["MovieID"].unique())]

    if p.empty:
        st.info("Ninguna película con 20 votos o más queda con estos filtros.")
    else:
        col1, col2 = st.columns(2)

        with col1:
            fig = px.scatter(p, x="votos", y="promedio", color="Segmento",
                             color_discrete_map=COLOR_SEGMENTO,
                             category_orders={"Segmento": ORDEN_SEGMENTOS}, opacity=0.65,
                             hover_name="Title",
                             hover_data={"dispersion": ":.2f", "Género": True, "Año": True,
                                         "votos": ":,", "promedio": ":.2f"},
                             labels={"votos": "Votos de la película (n°)",
                                     "promedio": "Promedio (estrellas)",
                                     "dispersion": "Dispersión (estrellas)"},
                             title="Segmentos según popularidad y valoración")
            st.plotly_chart(estilo(fig), width="stretch")

        with col2:
            # Radar: promedio de las variables ESCALADAS en cada segmento
            radar = escaladas.loc[p.index].groupby("Segmento")[VARIABLES].mean().reset_index()
            radar = radar.melt(id_vars="Segmento", var_name="Variable", value_name="Valor escalado")
            radar["Variable"] = radar["Variable"].map({"promedio": "Promedio", "votos": "Votos",
                                                       "dispersion": "Dispersión"})
            fig = px.line_polar(radar, r="Valor escalado", theta="Variable", color="Segmento",
                                line_close=True, color_discrete_map=COLOR_SEGMENTO,
                                category_orders={"Segmento": ORDEN_SEGMENTOS},
                                hover_name="Segmento", hover_data={"Valor escalado": ":.2f"},
                                title="Perfil de cada segmento (valores escalados)")
            fig.update_traces(fill="toself", opacity=0.55)
            estilo(fig).update_layout(margin=dict(l=70, r=70))   # espacio para las etiquetas
            st.plotly_chart(fig, width="stretch")

        # Tabla de perfiles
        st.subheader("Tabla de perfiles")
        tabla = p.groupby("Segmento").agg(
            Películas=("MovieID", "size"),
            Promedio=("promedio", "mean"),
            Votos_mediana=("votos", "median"),
            Dispersión=("dispersion", "mean"),
            Año_mediano=("Año", "median"),
            Género_dominante=("Género", lambda g: g.mode()[0]),
        ).reindex([s for s in ORDEN_SEGMENTOS if s in p["Segmento"].unique()]).reset_index()
        tabla.insert(2, "% películas", tabla["Películas"] / tabla["Películas"].sum() * 100)
        st.dataframe(tabla.round(2), width="stretch", hide_index=True)
        st.caption("Alta exposición (11,5%): promedio 3,84 y una mediana de 1.074 votos. "
                   "Valoración favorable (43,6%): casi la misma nota (3,67) con 206 votos "
                   "medianos y la menor dispersión: consenso sin masividad. Menor valoración "
                   "(44,9%): promedio 2,80 y la mayor dispersión; además de gustar menos, "
                   "generan más desacuerdo.")

        # Selector: detalle de un segmento (control local)
        elegido = st.selectbox("Ver el detalle de un segmento",
                               [s for s in ORDEN_SEGMENTOS if s in p["Segmento"].unique()])
        detalle = p[p["Segmento"] == elegido]
        d1, d2, d3 = st.columns(3)
        d1.metric("Películas del segmento", miles(len(detalle)))
        d2.metric("Promedio del segmento", f"{detalle['promedio'].mean():.2f} ★",
                  delta=f"{detalle['promedio'].mean() - p['promedio'].mean():+.2f} vs filtro")
        d3.metric("Votos medianos", miles(int(detalle["votos"].median())))
        top = detalle.nlargest(10, "votos").sort_values("votos")
        fig = px.bar(top, x="votos", y="Title", orientation="h", hover_name="Title",
                     hover_data={"promedio": ":.2f", "dispersion": ":.2f", "Title": False,
                                 "votos": ":,"},
                     labels={"votos": "Votos (n°)", "Title": "", "promedio": "Promedio",
                             "dispersion": "Dispersión"},
                     title=f"Las 10 películas más votadas de «{elegido}»")
        fig.update_traces(marker_color=COLOR_SEGMENTO[elegido])
        st.plotly_chart(estilo(fig), width="stretch")

        # Multidimensional: coordenadas paralelas con color continuo
        st.subheader("Coordenadas paralelas de las películas")
        fig = px.parallel_coordinates(p, dimensions=["promedio", "votos", "dispersion", "Año"],
                                      color="promedio", color_continuous_scale=ESCALA,
                                      labels={"promedio": "Promedio (estrellas)",
                                              "votos": "Votos (n°)",
                                              "dispersion": "Dispersión (estrellas)",
                                              "Año": "Año de estreno"},
                                      title="Cada línea es una película con 20 votos o más")
        st.plotly_chart(estilo(fig), width="stretch")
        st.caption("Las líneas doradas (promedio alto) pasan por dispersión baja y años de "
                   "estreno más antiguos; las rojas (promedio bajo), por dispersión alta y "
                   "estrenos recientes. La mala nota viene con desacuerdo.")

# ── 10. HALLAZGOS PRINCIPALES ────────────────────────────────
st.markdown("""
<div class="hallazgos">
<h3>Hallazgos principales</h3>
<ul>
<li><b>Popularidad y valoración miden cosas distintas:</b> se relacionan solo de forma moderada
(r = 0,38). Las películas masivas (alta exposición, 11,5%) son bien valoradas, pero las mejores
notas también aparecen en películas con pocos votos.</li>
<li><b>El promedio debe leerse junto con la cantidad de votos:</b> bajo 20 votos aparecen los
promedios extremos; por eso los rankings y la segmentación usan solo películas con 20 votos o más.</li>
<li><b>La mala nota viene con desacuerdo y tiene género:</b> el segmento de menor valoración tiene la
mayor dispersión; terror es el género peor evaluado y Film-Noir y documentales los mejores.</li>
<li><b>Sesgo de clásicos:</b> las películas antiguas reciben mejores notas porque solo se siguen
viendo las buenas, no porque el cine antiguo sea mejor.</li>
<li><b>Quién califica importa:</b> el público es mayoritariamente masculino y de 25 a 34 años,
y la nota promedio sube con la edad.</li>
</ul>
</div>
""", unsafe_allow_html=True)

st.write("")

# ── 11. TABLA DE DATOS (DESPLEGABLE) ─────────────────────────
with st.expander("Ver datos filtrados"):
    st.dataframe(dff[["Title", "Género", "Año", "Rating", "Sexo", "Edad", "Ocupación",
                      "Estado", "Segmento"]].head(1000),
                 width="stretch", hide_index=True)
    st.caption("Se muestran las primeras 1.000 filas de los datos filtrados.")
