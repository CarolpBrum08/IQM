import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
import zipfile
import io
import requests
import json

# PRIMEIRO comando Streamlit
st.set_page_config(layout="wide")

# ======= Carga de dados =======
@st.cache_data
def load_data():
    df = pd.read_excel("IQM_BRASIL_2025.xlsm", sheet_name="IQM_Qualificação", header=3)
    ranking = pd.read_excel("IQM_BRASIL_2025.xlsm", sheet_name="IQM_Ranking")
    return df, ranking

@st.cache_data
def load_geo():
    st.info("🔄 Baixando shapefile zipado do Dropbox...")

    url = "https://www.dropbox.com/scl/fi/9ykpfmts35d0ct0ufh7c6/BR_Microrregioes_2022.zip?rlkey=kjbpqi3f6aeun4ctscae02k9e&st=mer376fu&dl=1"

    r = requests.get(url)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall("micros")

    gdf = gpd.read_file("micros/BR_Microrregioes_2022.shp").to_crs(epsg=4326)
    gdf = gdf[['CD_MICRO', 'geometry']]
    return gdf

df, df_ranking = load_data()
gdf = load_geo()

# Ajustar tipos para merge
df["Código da Microrregião"] = df["Código da Microrregião"].astype(str)
gdf["CD_MICRO"] = gdf["CD_MICRO"].astype(str)

# Merge para juntar geometria e indicadores
geo_df = pd.merge(df, gdf, left_on="Código da Microrregião", right_on="CD_MICRO")

# ======= Interface =======
st.title("📊 Dashboard IQM - Microregiões do Brasil")

# Ordem invertida: Indicador primeiro, UF depois
indicadores = ["IQM FINAL", "Top 10 Microregiões (Ranking IQM)"]
ind_sel = st.selectbox("Selecione o Indicador:", indicadores)

ufs = sorted(geo_df["UF"].unique())
uf_sel = st.selectbox("Selecione um Estado (UF):", ufs)

# Modo normal
if ind_sel != "Top 10 Microregiões (Ranking IQM)":
    df_uf = geo_df[geo_df["UF"] == uf_sel]
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

    # Detalhes por Microrregião
    micros = sorted(df_uf["Microrregião"].unique())
    mic_sel = st.selectbox("Selecione uma Microrregião para detalhes:", micros)
    df_micro = df_uf[df_uf["Microrregião"] == mic_sel]
    st.write(df_micro.T.iloc[-4:])

    # Tabela completa
    with st.expander("📁 Ver tabela completa"):
        st.dataframe(df_uf, use_container_width=True)

else:
    st.subheader("🏆 Top 10 Microregiões - Ranking IQM (Brasil)")

    top10 = df_ranking.head(10)
    top10["Código da Microrregião"] = top10["Código da Microrregião"].astype(str)
    df_top10 = geo_df[geo_df["Código da Microrregião"].isin(top10["Código da Microrregião"])]

    # Pega os estados do top10 para exibir limites no mapa
    estados_top10 = df_top10["UF"].unique().tolist()
    df_estados = geo_df[geo_df["UF"].isin(estados_top10)].drop_duplicates(subset=["UF", "Código da Microrregião"])

    # Geojson geral para os estados do Top10 (usado como base)
    gdf_estados = gpd.GeoDataFrame(df_estados).set_index("Código da Microrregião")
    geojson_estados = json.loads(gdf_estados.to_json())

    # Geojson Top10 para preenchimento
    gdf_top10 = gpd.GeoDataFrame(df_top10).set_index("Código da Microrregião")
    geojson_top10 = json.loads(gdf_top10.to_json())

    # Criar figura com Plotly Graph Objects para duas camadas
    fig = go.Figure()

    # Camada 1: contorno dos estados do top10 (como base do mapa)
    fig.add_trace(go.Choropleth(
        geojson=geojson_estados,
        locations=gdf_estados.index,
        z=[0]*len(gdf_estados),  # cor neutra, só para mostrar limites
        colorscale=[[0, 'rgba(0,0,0,0)'], [1, 'rgba(0,0,0,0)']],  # transparente
        showscale=False,
        marker_line_width=1,
        marker_line_color='black',
        hoverinfo='skip',
    ))

    # Camada 2: preenchimento colorido do Top 10
    fig.add_trace(go.Choropleth(
        geojson=geojson_top10,
        locations=gdf_top10.index,
        z=gdf_top10["IQM FINAL"],
        colorscale="YlGnBu",
        colorbar_title="IQM FINAL",
        marker_line_width=1,
        marker_line_color='white',
        hoverinfo='location+z',
    ))

    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0})

    st.plotly_chart(fig, use_container_width=True)

    # Ranking do Top 10
    top10_view = df_top10[["Microrregião", "UF", "IQM FINAL"]].sort_values(by="IQM FINAL", ascending=False).reset_index(drop=True)
    top10_view.index += 1
    st.dataframe(top10_view.style.background_gradient(cmap="YlGnBu", subset=["IQM FINAL"]), use_container_width=True)
