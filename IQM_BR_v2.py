import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go
import plotly.express as px
import zipfile
import io
import requests
import json
import os

st.set_page_config(layout="wide")

# ======= Função para carregar dados Excel =======
@st.cache_data
def load_data():
    df = pd.read_excel("IQM_BRASIL_2025.xlsm", sheet_name="IQM_Qualificação", header=3)
    ranking = pd.read_excel("IQM_BRASIL_2025.xlsm", sheet_name="IQM_Ranking")
    return df, ranking

# ======= Função para carregar shapefile das microrregiões =======
@st.cache_data
def load_geo_micro():
    st.info("🔄 Baixando shapefile zipado do Dropbox (Microrregiões)...")
    url = "https://www.dropbox.com/scl/fi/9ykpfmts35d0ct0ufh7c6/BR_Microrregioes_2022.zip?rlkey=kjbpqi3f6aeun4ctscae02k9e&dl=1"
    r = requests.get(url)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall("micros")
    gdf = gpd.read_file("micros/BR_Microrregioes_2022.shp").to_crs(epsg=4326)
    gdf = gdf[['CD_MICRO', 'geometry']]
    gdf["CD_MICRO"] = gdf["CD_MICRO"].astype(str)
    return gdf

# ======= Função para carregar shapefile das UFs (estados) =======
@st.cache_data
def load_geo_ufs():
    st.info("🔄 Baixando shapefile zipado do IBGE (UFs)...")
    url = "https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2020/Brasil/UF/BR_UF_2020.zip"
    r = requests.get(url)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall("ufs")
    gdf = gpd.read_file("ufs/BR_UF_2020.shp").to_crs(epsg=4326)
    gdf = gdf[['CD_UF', 'NM_UF', 'geometry']]
    gdf["CD_UF"] = gdf["CD_UF"].astype(str)
    return gdf

# ======= Carregar dados =======
df, df_ranking = load_data()
gdf_micro = load_geo_micro()
gdf_ufs = load_geo_ufs()

# Preparar dados para merge
df["Código da Microrregião"] = df["Código da Microrregião"].astype(str)

# Merge microrregiões com geometria
geo_df = pd.merge(df, gdf_micro, left_on="Código da Microrregião", right_on="CD_MICRO")

# Título
st.title("📊 Dashboard IQM - Microregiões do Brasil")

# Filtro por estado
ufs = sorted(geo_df["UF"].unique())
uf_sel = st.selectbox("Selecione um Estado (UF):", ufs)

# Filtra dados do estado selecionado
df_uf = geo_df[geo_df["UF"] == uf_sel]

# Indicadores disponíveis: só IQM FINAL e Top 10
indicadores = ["IQM FINAL", "Top 10 Microregiões (Ranking IQM)"]
ind_sel = st.selectbox("Selecione o Indicador:", indicadores)

if ind_sel == "IQM FINAL":
    # Mostrar mapa normal por estado e indicador IQM FINAL
    gdf_uf = gpd.GeoDataFrame(df_uf).set_index("Código da Microrregião")
    geojson = json.loads(gdf_uf.to_json())

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

    # Ranking normal
    st.subheader("🏆 Ranking por " + ind_sel)
    rank = df_uf[["Microrregião", ind_sel]].sort_values(by=ind_sel, ascending=False).reset_index(drop=True)
    rank.index += 1
    st.dataframe(rank.style.background_gradient(cmap="YlGnBu", subset=[ind_sel]), use_container_width=True)

else:
    # Top 10 Brasil com contorno dos estados envolvidos
    st.subheader("🏆 Top 10 Microregiões - Ranking IQM (Brasil)")

    top10 = df_ranking.head(10)
    top10["Código da Microrregião"] = top10["Código da Microrregião"].astype(str)
    df_top10 = geo_df[geo_df["Código da Microrregião"].isin(top10["Código da Microrregião"])]

    # Estados do Top10
    estados_top10 = df_top10["UF"].unique().tolist()
    gdf_ufs_top = gdf_ufs[gdf_ufs["NM_UF"].isin(estados_top10)]

    # Geojson dos estados do Top10 para contorno
    geojson_ufs = json.loads(gdf_ufs_top.to_json())

    # Geojson das microrregiões Top10
    gdf_top10 = gpd.GeoDataFrame(df_top10).set_index("Código da Microrregião")
    geojson_top10 = json.loads(gdf_top10.to_json())

    fig = go.Figure()

    # Camada 1: contorno dos estados do Top10 (contorno preto)
    fig.add_trace(go.Choropleth(
        geojson=geojson_ufs,
        locations=gdf_ufs_top.index,
        z=[0]*len(gdf_ufs_top),  # sem cor, só contorno
        colorscale=[[0, 'rgba(0,0,0,0)'], [1, 'rgba(0,0,0,0)']],
        showscale=False,
        marker_line_width=1.5,
        marker_line_color='black',
        hoverinfo='skip',
    ))

    # Camada 2: microrregiões Top10 coloridas por IQM FINAL
    fig.add_trace(go.Choropleth(
        geojson=geojson_top10,
        locations=gdf_top10.index,
        z=gdf_top10["IQM FINAL"],
        colorscale="YlGnBu",
        colorbar_title="IQM FINAL",
        marker_line_width=0.5,
        marker_line_color='white',
        hoverinfo='location+z+text',
        text=gdf_top10["Microrregião"]
    ))

    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0})

    st.plotly_chart(fig, use_container_width=True)

    # Ranking Top 10
    top10_view = df_top10[["Microrregião", "UF", "IQM FINAL"]].sort_values(by="IQM FINAL", ascending=False).reset_index(drop=True)
    top10_view.index += 1
    st.dataframe(top10_view.style.background_gradient(cmap="YlGnBu", subset=["IQM FINAL"]), use_container_width=True)

# Detalhes microrregião para IQM FINAL
if ind_sel == "IQM FINAL":
    micros = sorted(df_uf["Microrregião"].unique())
    mic_sel = st.selectbox("Selecione uma Microrregião para detalhes:", micros)
    df_micro = df_uf[df_uf["Microrregião"] == mic_sel]
    st.write(df_micro.T.iloc[-4:])

# Mostrar tabela completa para o estado
with st.expander("📁 Ver tabela completa"):
    st.dataframe(df_uf, use_container_width=True)
