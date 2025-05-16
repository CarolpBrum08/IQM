import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px

# Carregamento dos dados
df = pd.read_csv("IQM_Qualificacao.csv")
gdf = gpd.read_file("microrregioes.shp")

# Título
st.title("📊 Dashboard IQM – Microrregiões do Brasil")

# Filtros (Indicador antes do Estado)
indicadores = ['IQM', 'DESVIO PADRÃO', 'CORREÇÃO', 'IQM FINAL']
indicador_selecionado = st.selectbox('Selecione o Indicador:', indicadores)

estados = sorted(df['UF'].unique())
estado_selecionado = st.selectbox('Selecione um Estado (UF):', estados)

# Filtrando dados pelo estado
df_estado = df[df['UF'] == estado_selecionado]
gdf_estado = gdf[gdf['CD_GEOCODM'].isin(df_estado['CD_GEOCODM'])]

# Mapa do estado selecionado
fig_estado = px.choropleth(
    gdf_estado,
    geojson=gdf_estado.geometry.__geo_interface__,
    locations=gdf_estado.index,
    color=df_estado[indicador_selecionado],
    hover_name=df_estado['NM_MICRO'],
    color_continuous_scale="YlGnBu",
)

fig_estado.update_geos(fitbounds="locations", visible=False)
st.plotly_chart(fig_estado, use_container_width=True)

# Título da seção Top 10
st.subheader(f"🏆 Top 10 Microrregiões - Ranking {indicador_selecionado} (Brasil)")

# Criar Top 10 nacional
top_10_df = df.sort_values(by=indicador_selecionado, ascending=False).head(10).copy()
top_10_df['Posição'] = range(1, 11)
top_10_codigos = top_10_df['CD_GEOCODM']

# Marcar cores só para Top 10 no mapa
gdf_mapa_brasil = gdf.copy()
gdf_mapa_brasil['COR_TOP10'] = gdf_mapa_brasil['CD_GEOCODM'].apply(
    lambda x: df.loc[df['CD_GEOCODM'] == x, indicador_selecionado].values[0]
    if x in top_10_codigos.values else None
)

# Mapa do Brasil com destaque Top 10
fig_top10 = px.choropleth(
    gdf_mapa_brasil,
    geojson=gdf_mapa_brasil.geometry.__geo_interface__,
    locations=gdf_mapa_brasil.index,
    color=gdf_mapa_brasil['COR_TOP10'],
    hover_name=gdf_mapa_brasil['NM_MICRO'],
    color_continuous_scale="YlGnBu",
)

fig_top10.update_geos(fitbounds="locations", visible=False)
fig_top10.update_layout(height=600, margin={"r":0,"t":30,"l":0,"b":0})

# Exibição lado a lado do mapa e da tabela
col1, col2 = st.columns([2, 1])

with col1:
    st.plotly_chart(fig_top10, use_container_width=True)

with col2:
    st.markdown("**📋 Ranking das Top 10 Microrregiões**")
    st.dataframe(
        top_10_df[['Posição', 'NM_MICRO', 'UF', indicador_selecionado]].reset_index(drop=True),
        use_container_width=True)
