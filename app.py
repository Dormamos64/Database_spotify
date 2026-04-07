import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Spotify Insights | 2010-2019", layout="wide")

# Estilo CSS para o "Visual Spotify Clean"
st.markdown("""
    <style>
    .metric-card {
        background-color: #181818;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #1DB954;
        margin-bottom: 10px;
    }
    .metric-card h3 {
        margin: 0;
        color: #1DB954;
    }
    .metric-card b {
        color: #FFFFFF;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. CARREGAMENTO E LIMPEZA (Lógica de tratamento de dados)
@st.cache_data
def get_data():
    # Carrega o CSV da pasta data
    df = pd.read_csv("data/top10s.csv", encoding='latin-1')
    
    # Limpeza 1: Remover coluna de índice fantasma do Kaggle
    if 'Unnamed: 0' in df.columns:
        df = df.drop(columns=['Unnamed: 0'])
    
    # Limpeza 2: Renomear colunas para Português/Clareza
    df.columns = ['Musica', 'Artista', 'Genero', 'Ano', 'BPM', 'Energia', 
                  'Dancabilidade', 'Loudness', 'Liveness', 'Valence', 
                  'Duracao', 'Acustica', 'Speechiness', 'Popularidade']
    
    # Limpeza 3: Tratamento de Gêneros (Agrupamento)
    # Pega a última palavra do gênero para simplificar (ex: 'pop', 'hip hop')
    df['Genero_Clean'] = df['Genero'].str.split().str[-1].str.title()
    
    return df

try:
    df = get_data()

    # 3. SIDEBAR / FILTROS
    st.sidebar.image("https://storage.googleapis.com/pr-newsroom-wp/1/2018/11/Spotify_Logo_RGB_Green.png", width=150)
    st.sidebar.title("Filtros do Dashboard")
    
    anos = st.sidebar.multiselect(
        "Selecione os Anos:", 
        options=sorted(df['Ano'].unique()), 
        default=sorted(df['Ano'].unique())
    )
    
    popularidade_min = st.sidebar.slider("Popularidade Mínima", 0, 100, 50)

    # Filtragem dos dados
    df_selection = df[(df['Ano'].isin(anos)) & (df['Popularidade'] >= popularidade_min)]

    # 4. HEADER COM MÉTRICAS (KPIs)
    st.title("🎵 Spotify Decade Insights")
    st.markdown(f"Análise de hits de 2010 a 2019 baseada no Spotify Web API.")

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"<div class='metric-card'><b>Artista N°1</b><br><h3>{df_selection['Artista'].mode()[0]}</h3></div>", unsafe_allow_html=True)
    with m2:
        st.markdown(f"<div class='metric-card'><b>Gênero Top</b><br><h3>{df_selection['Genero_Clean'].mode()[0]}</h3></div>", unsafe_allow_html=True)
    with m3:
        bpm_medio = int(df_selection['BPM'].mean())
        st.markdown(f"<div class='metric-card'><b>BPM Médio</b><br><h3>{bpm_medio}</h3></div>", unsafe_allow_html=True)
    with m4:
        pop_media = int(df_selection['Popularidade'].mean())
        st.markdown(f"<div class='metric-card'><b>Score Pop</b><br><h3>{pop_media}/100</h3></div>", unsafe_allow_html=True)

    st.markdown("---")

    # 5. GRÁFICOS DE RANKING
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("🏆 Top 10 Artistas com Mais Hits")
        top_artistas = df_selection['Artista'].value_counts().head(10).reset_index()
        fig_art = px.bar(top_artistas, x='count', y='Artista', orientation='h', 
                         color='count', color_continuous_scale='Greens',
                         template="plotly_dark")
        fig_art.update_layout(showlegend=False, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_art, use_container_width=True)

    with c2:
        st.subheader("🎸 Distribuição por Gênero")
        top_generos = df_selection['Genero_Clean'].value_counts().head(8).reset_index()
        fig_gen = px.pie(top_generos, values='count', names='Genero_Clean', 
                         hole=0.5, color_discrete_sequence=px.colors.sequential.Greens_r)
        fig_gen.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_gen, use_container_width=True)

    # 6. ANÁLISE TEMPORAL
    st.markdown("---")
    st.subheader("📈 Evolução das Características Musicais")
    
    # Agrupando por ano
    timeline = df_selection.groupby('Ano')[['Energia', 'Dancabilidade', 'Valence']].mean().reset_index()
    fig_line = px.line(timeline, x='Ano', y=['Energia', 'Dancabilidade', 'Valence'],
                       markers=True, color_discrete_sequence=['#1DB954', '#FFFFFF', '#454545'],
                       template="plotly_dark")
    st.plotly_chart(fig_line, use_container_width=True)

    # 7. TABELA E CORRELAÇÃO
    c3, c4 = st.columns([1, 2])
    
    with c3:
        st.subheader("🔥 Top 10 Músicas")
        top_musicas = df_selection.nlargest(10, 'Popularidade')[['Musica', 'Popularidade']]
        st.dataframe(top_musicas, use_container_width=True)

    with c4:
        st.subheader("🔍 Correlação entre Variáveis")
        corr = df_selection[['BPM', 'Energia', 'Dancabilidade', 'Valence', 'Popularidade']].corr()
        fig_corr = px.imshow(corr, text_auto=True, color_continuous_scale='Greens', template="plotly_dark")
        st.plotly_chart(fig_corr, use_container_width=True)

    # 8. RODAPÉ
    st.markdown("---")
    st.caption("Fonte: Kaggle | Dados processados com Pandas e Streamlit")

except FileNotFoundError:
    st.error("Arquivo 'top10s.csv' não encontrado na pasta 'data/'. Verifique o caminho!")
except Exception as e:
    st.error(f"Ocorreu um erro inesperado: {e}")