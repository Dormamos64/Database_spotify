import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ─────────────────────────────────────────
# 1. CONFIGURAÇÃO DA PÁGINA
# ─────────────────────────────────────────
st.set_page_config(
    page_title="Spotify Analytics 2010–2025",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────
# 2. ESTILO GLOBAL (Spotify Dark)
# ─────────────────────────────────────────
st.markdown("""
<style>
/* Cards de métricas customizados */
.metric-card {
    background: #181818;
    padding: 18px 20px;
    border-radius: 10px;
    border-left: 4px solid #1DB954;
    margin-bottom: 12px;
}
.metric-card h3  { margin: 0 0 4px; color: #1DB954; font-size: 1.15rem; }
.metric-card .artist { color: #b3b3b3; font-size: 0.85rem; margin: 0; }
.metric-card .info   { color: #ffffff; font-size: 0.8rem; margin: 4px 0 0; }

/* Oculta índice padrão em st.table */
thead tr th:first-child { display: none; }
tbody tr td:first-child  { display: none; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# 3. MAPA DE GÊNEROS (normalização manual)
# ─────────────────────────────────────────
GENERO_MAP = {
    "dance pop":        "Dance Pop",
    "pop":              "Pop",
    "hip hop":          "Hip Hop",
    "rap":              "Rap",
    "trap":             "Trap",
    "r&b":              "R&B",
    "edm":              "EDM",
    "electronic":       "Eletrônico",
    "indie pop":        "Indie Pop",
    "indie":            "Indie",
    "rock":             "Rock",
    "latin":            "Latin",
    "reggaeton":        "Reggaeton",
    "country":          "Country",
    "soul":             "Soul",
    "funk":             "Funk",
    "alternative":      "Alternativo",
    "alt z":            "Alt Z",
    "canadian pop":     "Pop",
    "australian pop":   "Pop",
    "electropop":       "Eletrônico",
    "synthpop":         "Eletrônico",
    "unknown":          "Outros",
}

def normalizar_genero(g: str) -> str:
    if pd.isna(g):
        return "Outros"
    g_lower = g.strip().lower()
    for key, val in GENERO_MAP.items():
        if key in g_lower:
            return val
    # fallback: última palavra capitalizada
    return g_lower.split()[-1].title()

# ─────────────────────────────────────────
# 4. CLASSIFICAÇÕES AUXILIARES
# ─────────────────────────────────────────
def classificar_era(ano: int) -> str:
    if ano <= 2014: return "2010–2014: Era Digital"
    if ano <= 2019: return "2015–2019: Era Streaming"
    return "2020–2025: Era TikTok"

def classificar_vibe(v: float) -> str:
    if v >= 75:   return "Muito alegre"
    if v >= 55:   return "Alegre"
    if v >= 40:   return "Neutra"
    if v >= 25:   return "Melancólica"
    return "Muito melancólica"

def classificar_bpm(bpm: float) -> str:
    if bpm < 90:   return "Lento (<90)"
    if bpm < 120:  return "Moderado (90–120)"
    if bpm < 150:  return "Rápido (120–150)"
    return "Muito rápido (150+)"

# ─────────────────────────────────────────
# 5. CARGA E LIMPEZA DE DADOS
# ─────────────────────────────────────────
@st.cache_data
def get_clean_data() -> pd.DataFrame:
    df = pd.read_csv("data/unified_top_songs_2010_2025.csv")
    df.columns = [
        "Musica", "Artista", "Genero", "Ano", "BPM",
        "Energia", "Dancabilidade", "Loudness", "Liveness",
        "Valence", "Duracao_Seg", "Acustica", "Speechiness", "Popularidade",
    ]

    # Filtro de período
    df = df[df["Ano"] >= 2010].copy()

    # Correções numéricas (garante tipos corretos)
    num_cols = ["BPM","Energia","Dancabilidade","Loudness","Liveness",
                "Valence","Duracao_Seg","Acustica","Speechiness","Popularidade"]
    df[num_cols] = df[num_cols].apply(pd.to_numeric, errors="coerce")
    df.dropna(subset=["Ano","Popularidade"], inplace=True)
    df["Ano"] = df["Ano"].astype(int)

    # Novas colunas derivadas
    df["Genero_Principal"] = df["Genero"].apply(normalizar_genero)
    df["Era"]              = df["Ano"].apply(classificar_era)
    df["antes_2015"]       = df["Ano"] < 2015          # True / False
    df["Vibe"]             = df["Valence"].apply(classificar_vibe)
    df["Ritmo"]            = df["BPM"].apply(classificar_bpm)
    df["Duracao_Min"]      = (df["Duracao_Seg"] / 60).round(2)

    return df


try:
    df = get_clean_data()

    # ─────────────────────────────────────────
    # 6. SIDEBAR
    # ─────────────────────────────────────────
    with st.sidebar:
        st.image(
            "https://storage.googleapis.com/pr-newsroom-wp/1/2018/11/Spotify_Logo_RGB_Green.png",
            width=120,
        )
        st.markdown("## Filtros Globais")

        pop_min = st.slider("Popularidade mínima", 0, 100, 50)

        eras_opcoes = sorted(df["Era"].unique())
        eras_sel = st.multiselect("Eras", eras_opcoes, default=eras_opcoes)

        anos_range = st.slider(
            "Intervalo de anos",
            int(df["Ano"].min()), int(df["Ano"].max()),
            (int(df["Ano"].min()), int(df["Ano"].max())),
        )

        st.markdown("---")
        st.caption(f"Dataset: {len(df):,} músicas | {df['Artista'].nunique():,} artistas")

    # Aplica filtros
    df_f = df[
        (df["Popularidade"] >= pop_min) &
        (df["Era"].isin(eras_sel)) &
        (df["Ano"] >= anos_range[0]) &
        (df["Ano"] <= anos_range[1])
    ].copy()

    # ─────────────────────────────────────────
    # 7. TÍTULO + KPIs GLOBAIS
    # ─────────────────────────────────────────
    st.title("🎵 Spotify Trends — Insights 2010–2025")

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Músicas", f"{len(df_f):,}")
    k2.metric("Artistas únicos", f"{df_f['Artista'].nunique():,}")
    k3.metric("Popularidade média", f"{df_f['Popularidade'].mean():.0f}")
    k4.metric("BPM médio", f"{df_f['BPM'].mean():.0f}")
    k5.metric("Duração média", f"{df_f['Duracao_Min'].mean():.1f} min")

    st.markdown("---")

    # ─────────────────────────────────────────
    # 8. ABAS
    # ─────────────────────────────────────────
    (
        tab_tendencias,
        tab_era_vs,
        tab_antes_depois,
        tab_generos,
        tab_artistas,
        tab_correlacao,
        tab_anual,
        tab_dados,
    ) = st.tabs([
        "📈 Tendências",
        "🏛️ Eras",
        "⚡ Antes vs Depois de 2015",
        "🎸 Gêneros",
        "🎤 Artistas",
        "🔗 Correlações & Sucesso",
        "📅 Por Ano",
        "📋 Dados",
    ])

    # ── ABA 1: TENDÊNCIAS ────────────────────
    with tab_tendencias:
        st.subheader("Evolução do Perfil Sonoro (médias anuais)")

        atributos = {
            "Valence":      "Valência (felicidade)",
            "Energia":      "Energia",
            "Dancabilidade":"Dançabilidade",
            "Acustica":     "Acústica",
            "Speechiness":  "Speechiness",
            "BPM":          "BPM",
            "Duracao_Min":  "Duração (min)",
        }

        attr_sel = st.multiselect(
            "Escolha atributos para comparar:",
            list(atributos.keys()),
            default=["Valence", "Energia", "Dancabilidade"],
            format_func=lambda x: atributos[x],
        )

        if attr_sel:
            evo = df_f.groupby("Ano")[attr_sel].mean().reset_index()
            evo_melted = evo.melt("Ano", var_name="Atributo", value_name="Valor")
            evo_melted["Atributo"] = evo_melted["Atributo"].map(atributos)
            fig_evo = px.line(
                evo_melted, x="Ano", y="Valor", color="Atributo",
                markers=True, template="plotly_dark",
                color_discrete_sequence=px.colors.qualitative.G10,
            )
            fig_evo.update_layout(legend_title="Atributo")
            st.plotly_chart(fig_evo, use_container_width=True)

        # Duração — destaque isolado
        st.markdown("#### ⏱️ Efeito TikTok: Duração média das músicas")
        dur = df_f.groupby("Ano")["Duracao_Seg"].mean().reset_index()
        fig_dur = px.area(
            dur, x="Ano", y="Duracao_Seg",
            template="plotly_dark",
            color_discrete_sequence=["#1DB954"],
            labels={"Duracao_Seg": "Duração (seg)"},
        )
        fig_dur.add_vline(x=2016, line_dash="dash", line_color="rgba(255,255,255,0.35)",
                          annotation_text="TikTok lançado", annotation_position="top right")
        st.plotly_chart(fig_dur, use_container_width=True)

    # ── ABA 2: ERAS ──────────────────────────
    with tab_era_vs:
        st.subheader("Comparação Técnica entre Eras")

        radar_cols = ["Energia", "Dancabilidade", "Valence", "Acustica", "Speechiness", "Liveness"]
        eras_radar = st.multiselect(
            "Eras no radar:",
            options=df["Era"].unique(),
            default=list(df["Era"].unique()),
        )

        df_era_f = df_f[df_f["Era"].isin(eras_radar)]

        # Cores bem distintas por era: verde / laranja / roxo
        CORES_ERA = {
            "2010–2014: Era Digital":   {"line": "#1DB954", "fill": "rgba(29,185,84,0.15)"},
            "2015–2019: Era Streaming": {"line": "#FF6B35", "fill": "rgba(255,107,53,0.15)"},
            "2020–2025: Era TikTok":    {"line": "#A855F7", "fill": "rgba(168,85,247,0.15)"},
        }

        if not df_era_f.empty:
            fig_radar = go.Figure()
            for era in eras_radar:
                sub = df_era_f[df_era_f["Era"] == era]
                if not sub.empty:
                    vals = [round(sub[c].mean(), 1) for c in radar_cols]
                    cor = CORES_ERA.get(era, {"line": "#ffffff", "fill": "rgba(255,255,255,0.1)"})
                    fig_radar.add_trace(go.Scatterpolar(
                        r=vals,
                        theta=radar_cols,
                        fill="toself",
                        fillcolor=cor["fill"],
                        name=era,
                        line=dict(color=cor["line"], width=2.5),
                    ))
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100],
                        tickfont=dict(size=10, color="#b3b3b3"),
                        gridcolor="rgba(255,255,255,0.1)",
                    ),
                    angularaxis=dict(tickfont=dict(size=12)),
                    bgcolor="rgba(0,0,0,0)",
                ),
                template="plotly_dark",
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom", y=-0.25,
                    xanchor="center", x=0.5,
                    font=dict(size=12),
                ),
                margin=dict(t=40, b=80),
            )
            st.plotly_chart(fig_radar, use_container_width=True)

        # Legenda visual de cores
        st.markdown("""
        <div style="display:flex;gap:24px;margin:-8px 0 16px;flex-wrap:wrap;">
            <span style="display:flex;align-items:center;gap:6px;font-size:13px;">
                <span style="width:12px;height:12px;border-radius:50%;background:#1DB954;display:inline-block;"></span>
                2010–2014: Era Digital
            </span>
            <span style="display:flex;align-items:center;gap:6px;font-size:13px;">
                <span style="width:12px;height:12px;border-radius:50%;background:#FF6B35;display:inline-block;"></span>
                2015–2019: Era Streaming
            </span>
            <span style="display:flex;align-items:center;gap:6px;font-size:13px;">
                <span style="width:12px;height:12px;border-radius:50%;background:#A855F7;display:inline-block;"></span>
                2020–2025: Era TikTok
            </span>
        </div>
        """, unsafe_allow_html=True)

        # Boxplots por era
        st.markdown("#### Distribuição de popularidade por era")
        fig_box = px.box(
            df_f, x="Era", y="Popularidade", color="Era",
            template="plotly_dark",
            color_discrete_map={
                "2010–2014: Era Digital":   "#1DB954",
                "2015–2019: Era Streaming": "#FF6B35",
                "2020–2025: Era TikTok":    "#A855F7",
            },
        )
        st.plotly_chart(fig_box, use_container_width=True)

    # ── ABA 3: ANTES vs DEPOIS 2015 ──────────
    with tab_antes_depois:
        st.subheader("⚡ Antes vs Depois de 2015 — Mudança no Perfil Sonoro")

        st.markdown(
            "Dividimos o dataset pela variável **`antes_2015`** (True/False) "
            "e comparamos as médias de cada atributo de áudio."
        )

        atribs_comp = ["Energia", "Dancabilidade", "Valence", "Acustica",
                       "Speechiness", "Liveness", "BPM", "Duracao_Min"]

        comp = (
            df_f.groupby("antes_2015")[atribs_comp]
            .mean()
            .reset_index()
        )
        comp["Período"] = comp["antes_2015"].map({True: "Antes de 2015", False: "2015 em diante"})

        comp_melted = comp.melt(
            id_vars="Período",
            value_vars=atribs_comp,
            var_name="Atributo",
            value_name="Média",
        )

        fig_comp = px.bar(
            comp_melted, x="Atributo", y="Média", color="Período",
            barmode="group", template="plotly_dark",
            color_discrete_map={
                "Antes de 2015":    "#b3b3b3",
                "2015 em diante":   "#1DB954",
            },
        )
        st.plotly_chart(fig_comp, use_container_width=True)

        # Tabela de diferenças
        st.markdown("#### Δ Variação absoluta (2015+ vs <2015)")
        antes = comp[comp["antes_2015"] == True].set_index("antes_2015")[atribs_comp].iloc[0]
        depois = comp[comp["antes_2015"] == False].set_index("antes_2015")[atribs_comp].iloc[0]
        delta = (depois - antes).round(2).reset_index()
        delta.columns = ["Atributo", "Δ Variação"]
        delta["Direção"] = delta["Δ Variação"].apply(lambda x: "▲ Subiu" if x > 0 else "▼ Caiu")
        st.dataframe(delta.sort_values("Δ Variação"), use_container_width=True, hide_index=True)

        # ── PERGUNTA ANALÍTICA ──
        st.markdown("---")
        st.markdown("### 🔍 Pergunta: Qual atributo mais separou as duas eras?")
        st.markdown(
            "Com base nas diferenças acima, o atributo com **maior variação absoluta** "
            "é aquele que melhor caracteriza a mudança sonora pré/pós-2015. "
            "Isso significa que as músicas da era streaming/TikTok se tornaram sonoramente "
            "distintas principalmente nessa dimensão — seja ficando mais dançantes, mais tristes, "
            "mais eletrônicas, ou mais curtas."
        )
        if not delta.empty:
            maior = delta.reindex(delta["Δ Variação"].abs().sort_values(ascending=False).index).iloc[0]
            st.success(
                f"**Maior mudança:** `{maior['Atributo']}` — variação de **{maior['Δ Variação']:+.2f}** "
                f"pontos ({maior['Direção']})"
            )

    # ── ABA 4: GÊNEROS ───────────────────────
    with tab_generos:
        st.subheader("Ranking de Gêneros Musicais")

        col_a, col_b = st.columns([2, 1])

        with col_a:
            top_gen = df_f["Genero_Principal"].value_counts().head(15).reset_index()
            top_gen.columns = ["Gênero", "Qtd"]
            fig_gen = px.bar(
                top_gen, x="Qtd", y="Gênero", orientation="h",
                color="Qtd", color_continuous_scale="Greens",
                template="plotly_dark",
            )
            fig_gen.update_layout(
                yaxis={"categoryorder": "total ascending"},
                coloraxis_showscale=False,
            )
            st.plotly_chart(fig_gen, use_container_width=True)

        with col_b:
            st.markdown("#### Distribuição de Vibe por Gênero")
            top5_gen = top_gen["Gênero"].head(5).tolist()
            vibe_gen = (
                df_f[df_f["Genero_Principal"].isin(top5_gen)]
                .groupby(["Genero_Principal", "Vibe"])
                .size()
                .reset_index(name="n")
            )
            fig_vibe = px.bar(
                vibe_gen, x="n", y="Genero_Principal", color="Vibe",
                orientation="h", template="plotly_dark",
                color_discrete_sequence=["#1DB954","#b3b3b3","#1ed760","#535353","#ffffff"],
            )
            st.plotly_chart(fig_vibe, use_container_width=True)

        # Evolução de gêneros ao longo do tempo
        st.markdown("#### Evolução dos Top 5 Gêneros ao longo dos anos")
        gen_ano = (
            df_f[df_f["Genero_Principal"].isin(top5_gen)]
            .groupby(["Ano", "Genero_Principal"])
            .size()
            .reset_index(name="n")
        )
        fig_gen_line = px.line(
            gen_ano, x="Ano", y="n", color="Genero_Principal",
            markers=True, template="plotly_dark",
        )
        st.plotly_chart(fig_gen_line, use_container_width=True)

    # ── ABA 5: ARTISTAS ──────────────────────
    with tab_artistas:
        st.subheader("🎤 Artistas em Destaque")

        col1, col2 = st.columns(2)

        # Explode artistas com múltiplos nomes separados por ";"
        df_artistas_exp = df_f.copy()
        df_artistas_exp["Artista"] = df_artistas_exp["Artista"].str.split(";")
        df_artistas_exp = df_artistas_exp.explode("Artista")
        df_artistas_exp["Artista"] = df_artistas_exp["Artista"].str.strip()
        df_artistas_exp = df_artistas_exp[df_artistas_exp["Artista"].str.len() > 0]

        with col1:
            st.markdown("#### Top 10 por número de músicas")
            top_art = df_artistas_exp["Artista"].value_counts().head(10).reset_index()
            top_art.columns = ["Artista", "Músicas"]
            fig_art = px.bar(
                top_art, x="Músicas", y="Artista", orientation="h",
                template="plotly_dark",
                color_discrete_sequence=["#1DB954"],
            )
            fig_art.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig_art, use_container_width=True)

        with col2:
            st.markdown("#### Top 10 por popularidade média")
            top_pop = (
                df_artistas_exp.groupby("Artista")["Popularidade"]
                .agg(["mean", "count"])
                .reset_index()
            )
            top_pop = top_pop[top_pop["count"] >= 2]  # mínimo 2 aparições
            top_pop = top_pop.nlargest(10, "mean")
            top_pop.columns = ["Artista", "Pop. Média", "Qtd"]
            fig_pop = px.bar(
                top_pop, x="Pop. Média", y="Artista", orientation="h",
                template="plotly_dark",
                color_discrete_sequence=["#1ed760"],
            )
            fig_pop.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig_pop, use_container_width=True)

        # Scatter: Energia vs Dançabilidade
        st.markdown("#### Energia × Dançabilidade × Popularidade")
        fig_scatter = px.scatter(
            df_f.sample(min(500, len(df_f))),  # max 500 pontos para performance
            x="Energia", y="Dancabilidade",
            size="Popularidade", color="Era",
            hover_data=["Musica", "Artista", "Ano"],
            template="plotly_dark",
            color_discrete_sequence=["#b3b3b3", "#1DB954", "#1ed760"],
            opacity=0.75,
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    # ── ABA 5b: CORRELAÇÕES & SUCESSO ────────
    with tab_correlacao:
        st.subheader("🔗 O que faz uma música ser popular?")
        st.markdown(
            "Analisamos a **correlação** entre cada atributo de áudio e a popularidade das músicas. "
            "Valores próximos de +1 indicam relação positiva forte, próximos de -1 indicam relação inversa."
        )

        atribs_corr = ["BPM", "Energia", "Dancabilidade", "Loudness", "Liveness",
                       "Valence", "Duracao_Min", "Acustica", "Speechiness"]

        df_corr = df_f[atribs_corr + ["Popularidade"]].dropna()

        # ── Heatmap de correlação completo ──
        corr_matrix = df_corr.corr().round(2)
        fig_heat = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns.tolist(),
            y=corr_matrix.columns.tolist(),
            colorscale=[
                [0.0,  "#4B1528"],
                [0.25, "#993556"],
                [0.5,  "#181818"],
                [0.75, "#0F6E56"],
                [1.0,  "#1DB954"],
            ],
            zmid=0,
            text=corr_matrix.values.round(2),
            texttemplate="%{text}",
            textfont={"size": 11, "color": "white"},
            hovertemplate="<b>%{x}</b> × <b>%{y}</b><br>Correlação: %{z}<extra></extra>",
            showscale=True,
            colorbar=dict(
                title="Correlação",
                tickvals=[-1, -0.5, 0, 0.5, 1],
                ticktext=["-1", "-0.5", "0", "+0.5", "+1"],
                len=0.8,
            ),
        ))
        fig_heat.update_layout(
            template="plotly_dark",
            margin=dict(l=10, r=10, t=30, b=10),
            height=480,
        )
        st.plotly_chart(fig_heat, use_container_width=True)

        # ── Barras: correlação de cada atributo com popularidade ──
        st.markdown("#### Força de cada atributo na popularidade")
        corr_pop = (
            df_corr.drop(columns=["Popularidade"])
            .apply(lambda col: col.corr(df_corr["Popularidade"]))
            .reset_index()
        )
        corr_pop.columns = ["Atributo", "Correlação"]
        corr_pop = corr_pop.sort_values("Correlação", ascending=True)
        corr_pop["Cor"] = corr_pop["Correlação"].apply(
            lambda x: "#1DB954" if x > 0 else "#E24B4A"
        )
        corr_pop["Direção"] = corr_pop["Correlação"].apply(
            lambda x: "Positiva" if x > 0 else "Negativa"
        )

        fig_corr_bar = go.Figure(go.Bar(
            x=corr_pop["Correlação"],
            y=corr_pop["Atributo"],
            orientation="h",
            marker_color=corr_pop["Cor"].tolist(),
            text=corr_pop["Correlação"].round(3).astype(str),
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>Correlação com popularidade: %{x:.3f}<extra></extra>",
        ))
        fig_corr_bar.update_layout(
            template="plotly_dark",
            xaxis=dict(title="Correlação com Popularidade", range=[-1, 1], zeroline=True,
                       zerolinecolor="rgba(255,255,255,0.3)", zerolinewidth=1),
            yaxis=dict(title=""),
            height=360,
            margin=dict(l=10, r=60, t=20, b=40),
        )
        st.plotly_chart(fig_corr_bar, use_container_width=True)

        # ── Insight automático ──
        mais_positivo = corr_pop[corr_pop["Correlação"] > 0].nlargest(1, "Correlação")
        mais_negativo = corr_pop[corr_pop["Correlação"] < 0].nsmallest(1, "Correlação")

        col_ins1, col_ins2 = st.columns(2)
        with col_ins1:
            if not mais_positivo.empty:
                attr = mais_positivo.iloc[0]["Atributo"]
                val  = mais_positivo.iloc[0]["Correlação"]
                st.success(f"**{attr}** tem a correlação positiva mais forte com popularidade ({val:+.3f})")
        with col_ins2:
            if not mais_negativo.empty:
                attr = mais_negativo.iloc[0]["Atributo"]
                val  = mais_negativo.iloc[0]["Correlação"]
                st.error(f"**{attr}** tem a correlação negativa mais forte com popularidade ({val:+.3f})")

        # ── Scatter interativo: usuário escolhe atributo ──
        st.markdown("#### Explore: atributo × popularidade")
        attr_escolhido = st.selectbox(
            "Escolha o atributo para explorar:",
            options=atribs_corr,
            index=atribs_corr.index("Dancabilidade") if "Dancabilidade" in atribs_corr else 0,
        )
        fig_exp = px.scatter(
            df_f.dropna(subset=[attr_escolhido, "Popularidade"]).sample(min(600, len(df_f))),
            x=attr_escolhido,
            y="Popularidade",
            color="Era",
            hover_data=["Musica", "Artista", "Ano"],
            trendline="ols",
            template="plotly_dark",
            color_discrete_map={
                "2010–2014: Era Digital":   "#1DB954",
                "2015–2019: Era Streaming": "#FF6B35",
                "2020–2025: Era TikTok":    "#A855F7",
            },
            opacity=0.65,
            labels={attr_escolhido: attr_escolhido, "Popularidade": "Popularidade"},
        )
        fig_exp.update_layout(height=420)
        st.plotly_chart(fig_exp, use_container_width=True)
        st.caption("A linha de tendência (OLS) mostra a direção geral da correlação para cada era.")

    # ── ABA 6: POR ANO ───────────────────────
    with tab_anual:
        st.subheader("Análise por Ano")

        ano_alvo = st.select_slider(
            "Arraste para escolher o ano:",
            options=sorted(df_f["Ano"].unique()),
        )
        df_ano = df_f[df_f["Ano"] == ano_alvo]

        if df_ano.empty:
            st.warning("Nenhuma música encontrada para este ano com os filtros atuais.")
        else:
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                top = df_ano.nlargest(1, "Popularidade").iloc[0]
                st.markdown(
                    f"<div class='metric-card'>"
                    f"<b class='info'>🏆 Maior hit de {ano_alvo}</b>"
                    f"<h3>{top['Musica']}</h3>"
                    f"<p class='artist'>{top['Artista']}</p>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            with m2:
                genero_top = df_ano["Genero_Principal"].mode()[0]
                st.markdown(
                    f"<div class='metric-card'>"
                    f"<b class='info'>🎸 Gênero dominante</b>"
                    f"<h3>{genero_top}</h3>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            with m3:
                vibe_top = df_ano["Vibe"].mode()[0]
                st.markdown(
                    f"<div class='metric-card'>"
                    f"<b class='info'>🌡️ Vibe predominante</b>"
                    f"<h3>{vibe_top}</h3>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            with m4:
                bpm_medio = df_ano["BPM"].mean()
                st.markdown(
                    f"<div class='metric-card'>"
                    f"<b class='info'>🥁 BPM médio</b>"
                    f"<h3>{bpm_medio:.0f} BPM</h3>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            col_l, col_r = st.columns([3, 2])
            with col_l:
                st.markdown(f"#### Top 10 músicas de {ano_alvo}")
                top10 = df_ano.nlargest(10, "Popularidade")[
                    ["Musica", "Artista", "Genero_Principal", "Popularidade", "Vibe", "Duracao_Min"]
                ].rename(columns={"Genero_Principal": "Gênero", "Duracao_Min": "Duração (min)"})
                st.dataframe(top10, use_container_width=True, hide_index=True)

            with col_r:
                st.markdown(f"#### Distribuição de Vibe em {ano_alvo}")
                vibe_dist = df_ano["Vibe"].value_counts().reset_index()
                vibe_dist.columns = ["Vibe", "n"]
                fig_pie = px.pie(
                    vibe_dist, names="Vibe", values="n",
                    template="plotly_dark",
                    color_discrete_sequence=["#1DB954","#1ed760","#b3b3b3","#535353","#ffffff"],
                    hole=0.4,
                )
                fig_pie.update_traces(textposition="inside", textinfo="percent+label")
                st.plotly_chart(fig_pie, use_container_width=True)

    # ── ABA 7: DADOS ─────────────────────────
    with tab_dados:
        st.subheader("Dataset Filtrado")

        # Colunas exibidas
        cols_show = [
            "Musica","Artista","Genero_Principal","Ano","Era",
            "antes_2015","Popularidade","BPM","Ritmo",
            "Energia","Dancabilidade","Valence","Vibe",
            "Acustica","Speechiness","Duracao_Min",
        ]
        st.dataframe(
            df_f[cols_show].sort_values("Popularidade", ascending=False),
            use_container_width=True,
            hide_index=True,
        )
        st.caption(f"{len(df_f):,} músicas exibidas com os filtros atuais.")

        # Download
        csv = df_f[cols_show].to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Baixar CSV filtrado",
            data=csv,
            file_name="spotify_filtered.csv",
            mime="text/csv",
        )

except FileNotFoundError:
    st.error(
        "Arquivo `data/unified_top_songs_2010_2025.csv` não encontrado. "
        "Certifique-se de que o CSV está na pasta `data/` ao lado do script."
    )
except Exception as e:
    st.error(f"Erro inesperado: {e}")
    st.exception(e)