
import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import json
import zipfile
import io
import os
import requests


# PRIMEIRO comando Streamlit
st.set_page_config(layout="wide")

# ======= Carga de dados =======
@st.cache_data
def load_data():
    df = pd.read_excel("IQM_BRASIL_2025.xlsm", sheet_name="IQM_Qualificação", header=3)
    return df

@st.cache_data
def load_geo():
    # Link direto para download no Google Drive
    url = "https://drive.google.com/uc?export=download&id=14TwF5uPra8XssUfwwKGiSPdJY4vkTHGT"

    st.write("🔄 Baixando shapefile das microrregiões. Aguarde...")

    # Faz o download
    r = requests.get(url)
    z = zipfile.ZipFile(io.BytesIO(r.content))

    # Extrai para uma pasta temporária
    extract_path = "shapefile_temp"
    z.extractall(extract_path)

    # Encontra o arquivo .shp
    shp_file = [f for f in os.listdir(extract_path) if f.endswith(".shp")][0]
    full_path = os.path.join(extract_path, shp_file)

    # Carrega o GeoDataFrame
    gdf = gpd.read_file(full_path).to_crs(epsg=4326)
    gdf = gdf[['CD_MICRO', 'geometry']]
    return gdf
df = load_data()
gdf = load_geo()

# Ajustar tipos para merge
df["Código da Microrregião"] = df["Código da Microrregião"].astype(str)
gdf["CD_MICRO"] = gdf["CD_MICRO"].astype(str)

# Merge para juntar geometria e indicadores
geo_df = pd.merge(df, gdf, left_on="Código da Microrregião", right_on="CD_MICRO")

# ======= Interface =======
st.title("📊 Dashboard IQM - Microregiões do Brasil")

# Filtro por Estado
ufs = sorted(geo_df["UF"].unique())
uf_sel = st.selectbox("Selecione um Estado (UF):", ufs)
df_uf = geo_df[geo_df["UF"] == uf_sel]

# Seleção de indicador
indicadores = ["IQM", "Desvio Padrão", "Correção", "IQM FINAL"]
ind_sel = st.selectbox("Selecione o Indicador:", indicadores)

# Preparar GeoJSON
gdf_uf = gpd.GeoDataFrame(df_uf).set_index("Código da Microrregião")
geojson = json.loads(gdf_uf.to_json())

# Mapa
st.subheader(f"{ind_sel} - Microregiões de {uf_sel}")
fig = px.choropleth(
    df_uf,
    geojson=geojson,
    locations="Código da Microrregião",
    color=ind_sel,
    hover_name="Microrregião",
    projection="mercator",
    color_continuous_scale="YlGnBu"
)
fig.update_geos(fitbounds="locations", visible=False)
fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
st.plotly_chart(fig, use_container_width=True)

# Ranking
st.subheader("🏆 Ranking por " + ind_sel)
rank = df_uf[["Microrregião", ind_sel]].sort_values(by=ind_sel, ascending=False).reset_index(drop=True)
rank.index += 1
st.dataframe(rank.style.background_gradient(cmap="YlGnBu", subset=[ind_sel]), use_container_width=True)

# Detalhes por Microrregião
micros = sorted(df_uf["Microrregião"].unique())
mic_sel = st.selectbox("Selecione uma Microrregião para detalhes:", micros)
df_micro = df_uf[df_uf["Microrregião"] == mic_sel]
st.write(df_micro.T.iloc[-4:])

# Tabela completa
with st.expander("📑 Ver tabela completa"):
    st.dataframe(df_uf, use_container_width=True)
