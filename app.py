import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Configuração da Página
st.set_page_config(page_title="Spotify Analytics: 2010-2025", layout="wide")

# 2. Estilo Spotify Dark
st.markdown("""
    <style>
    .metric-card {
        background-color: #181818; padding: 20px; border-radius: 10px;
        border-left: 5px solid #1DB954; margin-bottom: 10px;
    }
    .metric-card h3 { margin: 0; color: #1DB954; font-size: 1.2rem; }
    .metric-card b { color: #FFFFFF; font-size: 0.9rem; }
    .metric-card p { margin: 0; color: #b3b3b3; font-size: 0.8rem; }
    </style>
    """, unsafe_allow_html=True)

# 3. Carregamento e Limpeza
@st.cache_data
def get_clean_data():
    df = pd.read_csv("data/unified_top_songs_2010_2025.csv")
    df.columns = ['Musica', 'Artista', 'Genero', 'Ano', 'BPM', 'Energia', 
                  'Dancabilidade', 'Loudness', 'Liveness', 'Valence', 
                  'Duracao_Seg', 'Acustica', 'Speechiness', 'Popularidade']

    # LIMPEZA: Foco na era moderna e correção de gêneros
    df = df[df['Ano'] >= 2010].copy()
    df['Genero'] = df['Genero'].replace('unknown', 'Outros/Indefinido')
    df['Genero_Principal'] = df['Genero'].str.split().str[-1].str.title()
    
    def definir_era(ano):
        if 2010 <= ano <= 2014: return "2010-2014: Era Digital"
        if 2015 <= ano <= 2019: return "2015-2019: Era Streaming"
        return "2020-2025: Era TikTok"
    
    df['Era'] = df['Ano'].apply(definir_era)
    df['Vibe'] = df['Valence'].apply(lambda x: 'Alegre' if x > 60 else ('Melancólica' if x < 40 else 'Neutra'))
    df['Duracao_Min'] = (df['Duracao_Seg'] / 60).round(2)
    
    return df

try:
    df = get_clean_data()

    # --- SIDEBAR GLOBAL ---
    st.sidebar.image("https://storage.googleapis.com/pr-newsroom-wp/1/2018/11/Spotify_Logo_RGB_Green.png", width=120)
    st.sidebar.title("Filtros Gerais")
    pop_min = st.sidebar.slider("Popularidade Mínima", 0, 100, 50)
    df_filtered = df[df['Popularidade'] >= pop_min]

    st.title("🎵 Spotify Trends: Insights 2010-2025")
    
    # --- ABAS ---
    tab_insights, tab_eras, tab_generos, tab_anual, tab_dados = st.tabs([
        "💡 Insights de Mercado", "🏛️ Visão por Eras", "🎸 Análise de Gêneros", "📅 Visão por Ano", "📋 Tabela"
    ])

    # --- ABA 0: INSIGHTS (Permanecem as respostas A, B, D) ---
    with tab_insights:
        st.subheader("Tendências Globais")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**A) Evolução da Felicidade (Valência)**")
            val_mean = df.groupby('Ano')['Valence'].mean().reset_index()
            fig_a = px.line(val_mean, x='Ano', y='Valence', markers=True, template="plotly_dark", color_discrete_sequence=['#1DB954'])
            st.plotly_chart(fig_a, use_container_width=True)
        with c2:
            st.markdown("**B) Duração Média (Efeito TikTok)**")
            dur_mean = df.groupby('Ano')['Duracao_Seg'].mean().reset_index()
            fig_b = px.area(dur_mean, x='Ano', y='Duracao_Seg', template="plotly_dark", color_discrete_sequence=['#1DB954'])
            st.plotly_chart(fig_b, use_container_width=True)
        with c3:
            st.markdown("**D) Distribuição de BPM**")
            fig_d = px.histogram(df_filtered, x="BPM", nbins=20, template="plotly_dark", color_discrete_sequence=['#1DB954'])
            st.plotly_chart(fig_d, use_container_width=True)

    # --- ABA 1: VISÃO POR ERAS (Apenas com seleção) ---
    with tab_eras:
        st.subheader("Comparação Técnica entre Eras")
        eras_selecionadas = st.multiselect("Selecione as Eras para visualizar no gráfico:", 
                                         options=df['Era'].unique(), 
                                         default=df['Era'].unique())
        
        df_era_comp = df_filtered[df_filtered['Era'].isin(eras_selecionadas)]
        
        if not df_era_comp.empty:
            radar_cols = ['Energia', 'Dancabilidade', 'Valence', 'Acustica', 'Speechiness']
            fig_radar = go.Figure()
            for era in eras_selecionadas:
                subset = df_era_comp[df_era_comp['Era'] == era]
                if not subset.empty:
                    vals = [subset[c].mean() for c in radar_cols]
                    fig_radar.add_trace(go.Scatterpolar(r=vals, theta=radar_cols, fill='toself', name=era))
            fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), template="plotly_dark")
            st.plotly_chart(fig_radar, use_container_width=True)

    # --- ABA 2: GÊNEROS (Com gráfico em barras) ---
    with tab_generos:
        st.subheader("Ranking de Gêneros Musicais")
        
        # Preparando dados para o gráfico de barras
        top_gen = df_filtered['Genero_Principal'].value_counts().head(15).reset_index()
        top_gen.columns = ['Gênero', 'Quantidade']
        
        fig_gen_bar = px.bar(top_gen, 
                             x='Quantidade', 
                             y='Gênero', 
                             orientation='h',
                             title="Top 15 Gêneros mais frequentes",
                             color='Quantidade',
                             color_continuous_scale='Greens',
                             template="plotly_dark")
        
        fig_gen_bar.update_layout(yaxis={'categoryorder':'total ascending'}) # Ordena da maior para menor
        st.plotly_chart(fig_gen_bar, use_container_width=True)
        
        st.info("💡 O gráfico de barras facilita a comparação direta entre os gêneros predominantes no seu filtro atual.")

    # --- ABA 3: VISÃO POR ANO ---
    with tab_anual:
        ano_alvo = st.select_slider("Arraste para mudar o ano:", options=sorted(df['Ano'].unique()))
        df_ano = df_filtered[df_filtered['Ano'] == ano_alvo]
        if not df_ano.empty:
            m1, m2 = st.columns(2)
            with m1:
                top = df_ano.nlargest(1, 'Popularidade').iloc[0]
                st.markdown(f"<div class='metric-card'><b>Maior Hit de {ano_alvo}</b><h3>{top['Musica']}</h3><p>{top['Artista']}</p></div>", unsafe_allow_html=True)
            with m2:
                st.markdown(f"<div class='metric-card'><b>Gênero em Alta</b><h3>{df_ano['Genero_Principal'].mode()[0]}</h3></div>", unsafe_allow_html=True)
            st.table(df_ano.nlargest(10, 'Popularidade')[['Musica', 'Artista', 'Popularidade']])

    # --- ABA 4: TABELA ---
    with tab_dados:
        st.subheader("Dataset Filtrado")
        st.dataframe(df_filtered, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Erro ao processar: {e}")