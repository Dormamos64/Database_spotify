import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuração da Página
st.set_page_config(page_title="Spotify Decade Analytics", layout="wide")

# Estilo Visual (Spotify Dark)
st.markdown("""
    <style>
    .metric-card {
        background-color: #181818;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #1DB954;
        margin-bottom: 10px;
    }
    .metric-card h3 { margin: 0; color: #1DB954; font-size: 1.2rem; }
    .metric-card b { color: #FFFFFF; font-size: 0.9rem; }
    .metric-card p { margin: 0; color: #b3b3b3; font-size: 0.8rem; }
    </style>
    """, unsafe_allow_html=True)

# Carregamento e Tratamento de Dados
@st.cache_data
def get_data():
    df = pd.read_csv("data/top10s.csv", encoding='latin-1')
    if 'Unnamed: 0' in df.columns:
        df = df.drop(columns=['Unnamed: 0'])
    
    # Renomeação de colunas
    df.columns = ['Musica', 'Artista', 'Genero', 'Ano', 'BPM', 'Energia', 
                  'Dancabilidade', 'Loudness', 'Liveness', 'Valence', 
                  'Duracao', 'Acustica', 'Speechiness', 'Popularidade']
    
    # Limpeza de gêneros e conversão de tempo
    df['Genero_Clean'] = df['Genero'].str.split().str[-1].str.title()
    df['Duracao_Min'] = (df['Duracao'] / 60).round(2)
    return df

try:
    df = get_data()

    # Painel Lateral (Filtros)
    st.sidebar.image("https://storage.googleapis.com/pr-newsroom-wp/1/2018/11/Spotify_Logo_RGB_Green.png", width=150)
    st.sidebar.title("Configurações")
    
    anos = st.sidebar.multiselect("Anos:", options=sorted(df['Ano'].unique()), default=sorted(df['Ano'].unique()))
    artistas_filtro = st.sidebar.multiselect("Filtrar por Artista:", options=sorted(df['Artista'].unique()))
    pop_min = st.sidebar.slider("Popularidade Mínima", 0, 100, 50)

    # Aplicação dos Filtros
    df_selection = df[(df['Ano'].isin(anos)) & (df['Popularidade'] >= pop_min)]
    if artistas_filtro:
        df_selection = df_selection[df_selection['Artista'].isin(artistas_filtro)]

    # Cabeçalho e Métricas de Topo
    st.title("🎵 Spotify Decade Analytics (2010-2019)")
    
    top_art = df_selection['Artista'].mode()[0]
    top_mus = df_selection[df_selection['Artista'] == top_art].nlargest(1, 'Popularidade').iloc[0]['Musica']

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"<div class='metric-card'><b>Artista em Destaque</b><h3>{top_art}</h3><p>Hit: {top_mus}</p></div>", unsafe_allow_html=True)
    with m2:
        st.markdown(f"<div class='metric-card'><b>Gênero Top</b><h3>{df_selection['Genero_Clean'].mode()[0]}</h3><p>Mais frequente</p></div>", unsafe_allow_html=True)
    with m3:
        st.markdown(f"<div class='metric-card'><b>Dançabilidade Média</b><h3>{int(df_selection['Dancabilidade'].mean())}%</h3><p>Potencial de pista</p></div>", unsafe_allow_html=True)
    with m4:
        st.markdown(f"<div class='metric-card'><b>Total de Hits</b><h3>{len(df_selection)}</h3><p>Músicas filtradas</p></div>", unsafe_allow_html=True)

    st.markdown("---")

    # Organização por Abas
    tab1, tab2, tab3 = st.tabs(["📊 Rankings", "🎯 DNA Técnico", "📂 Dados"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🏆 Maiores Hitmakers")
            fig_art = px.bar(df_selection['Artista'].value_counts().head(10).reset_index(), 
                             x='count', y='Artista', orientation='h', color='count', 
                             color_continuous_scale='Greens', template="plotly_dark")
            st.plotly_chart(fig_art, use_container_width=True)
        
        with c2:
            st.subheader("🔥 Maiores Hits por Artista")
            top_hits = df_selection.sort_values('Popularidade', ascending=False).drop_duplicates('Artista').head(10)
            st.dataframe(top_hits[['Artista', 'Musica', 'Popularidade']], hide_index=True, use_container_width=True)

        st.subheader("⏲️ Duração das Músicas por Ano")
        fig_box = px.box(df_selection, x='Ano', y='Duracao_Min', color='Ano', 
                        color_discrete_sequence=px.colors.sequential.Greens, template="plotly_dark")
        st.plotly_chart(fig_box, use_container_width=True)

    with tab2:
        c3, c4 = st.columns(2)
        with c3:
            st.subheader("🔍 Mapa de Correlação")
            corr = df_selection[['BPM', 'Energia', 'Dancabilidade', 'Valence', 'Popularidade']].corr().round(2)
            fig_corr = px.imshow(corr, text_auto=True, color_continuous_scale='Greens', template="plotly_dark")
            st.plotly_chart(fig_corr, use_container_width=True)
        
        with c4:
            st.subheader("🎯 Perfil de Áudio Médio")
            radar_cols = ['Energia', 'Dancabilidade', 'Valence', 'Acustica', 'Speechiness']
            radar_vals = [df_selection[c].mean() for c in radar_cols]
            fig_radar = go.Figure(data=go.Scatterpolar(r=radar_vals, theta=radar_cols, fill='toself', line_color='#1DB954'))
            fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), template="plotly_dark")
            st.plotly_chart(fig_radar, use_container_width=True)

    with tab3:
        st.subheader("📋 Tabela Completa (Exportável)")
        st.dataframe(df_selection, use_container_width=True)
        
        # Botão para exportar CSV
        csv = df_selection.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Baixar Dados Tratados", data=csv, file_name='spotify_final.csv', mime='text/csv')

except Exception as e:
    st.error(f"Erro: {e}")

st.caption("Fonte: Kaggle - Top Spotify Songs from 2010-2019 by Leonardo Henrique | Equipe : Gabriel Amaral, Refael Tavares, Felipe Mesquita.")