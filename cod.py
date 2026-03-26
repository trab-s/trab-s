import streamlit as st
from supabase import create_client
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import base64
import os
import io

st.set_page_config(page_title="Painel de Análise", layout="wide")

# Supabase
SUPABASE_URL = "https://jmxkzrzevnchfbbzfpun.supabase.co"    
SUPABASE_KEY = "sb_publishable_ggxYOSD-3KmSSiWYDrcshQ_T53QnyJz"

if "foto" not in st.session_state:
    st.session_state.foto = None

CONFIG_GRAFICOS = {
    'cores_barras': ['#8B0000', '#FF4500', '#FFD700', '#32CD32', '#4682B4'],
    'cores_pizza': ['#8B0000', '#FF4500', '#FFD700', '#32CD32', '#4682B4'],
    'cores_ranking': ['#FFD700', '#FFA500', '#FF8C00', '#FF6347', '#FF4500', '#DC143C', '#B22222', '#8B0000', '#696969', '#2F4F4F'], # Top 10
    'labels_notas': ['Nota 1', 'Nota 2', 'Nota 3', 'Nota 4', 'Nota 5'], # Labels personalizados
    'titulos': {
        'servico_barras': '📊 Frequência Notas - Serviço',
        'servico_pizza': '📈 Distribuição Notas - Serviço', 
        'func_barras': '📊 Frequência Notas - Funcionário',
        'func_pizza': '📈 Distribuição Notas - Funcionário',
        'ranking': '🏆 TOP 10 Funcionários - Ranking'
    }
}

# inicializar banco (se não existir)
def init_db():
    pass  

# Converter imagem para base64
def get_base64(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Definir o fundo
def set_background(png_file):
    bin_str = get_base64(png_file)
    page_bg_img = '''
    <style>
    .stApp {
    background-image: url("data:image/png;base64,%s");
    background-size: cover;
    background-repeat: no-repeat;
    background-attachment: fixed;
    }
    </style>
    ''' % bin_str
    st.markdown(page_bg_img, unsafe_allow_html=True)

def add_logo_top_right(image_path):
    img_base64 = get_base64(image_path)
   
    st.markdown(
        f"""
        <style>
        .logo-top-right {{
            position: absolute;
            top: 40px;
            right: 20px;
            width: 140px;
            z-index: 100;
        }}
        </style>

        <img src="data:image/png;base64,{img_base64}" class="logo-top-right">
        """,
        unsafe_allow_html=True)

def conectar():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def carregar_dados_completos():
    conn = conectar()
    
    func_resp = conn.table('funcionarios').select("*").execute()
    func = pd.DataFrame(func_resp.data or [])
    
    notas_resp = conn.table('notas').select("*, funcionarios(nome, cargo)").execute()
    notas_list = notas_resp.data or []
    
    if notas_list:
        notas = pd.json_normalize(notas_list)

        if 'funcionarios.nome' in notas.columns:
            notas = notas.rename(columns={'funcionarios.nome': 'nome'})
            
        elif 'funcionarios' in notas.columns:
            notas['nome'] = notas['funcionarios'].apply(lambda x: x['nome'] if x else None)
            notas = notas.drop('funcionarios', axis=1)
    else:
        notas = pd.DataFrame()
    
    obs_resp = conn.table('observacoes').select("*, funcionarios(nome)").execute()
    obs_list = obs_resp.data or []
    
    if obs_list:
        obs = pd.json_normalize(obs_list)

        if 'funcionarios.nome' in obs.columns:
            obs = obs.rename(columns={'funcionarios.nome': 'nome'})
        elif 'funcionarios' in obs.columns:
            obs['nome'] = obs['funcionarios'].apply(lambda x: x['nome'] if x else None)
            obs = obs.drop('funcionarios', axis=1)
    else:
        obs = pd.DataFrame()
    
    return notas, obs, func

def baixar_csv(df, nome_arquivo):
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, encoding='utf-8')
    csv_data = csv_buffer.getvalue().encode('utf-8')
    st.download_button(
        label=f"📥 Baixar {nome_arquivo}",
        data=csv_data,
        file_name=nome_arquivo,
        mime='text/csv')

def grafico_barras_frequencia(df, colunas, titulo=""):
    fig, ax = plt.subplots(figsize=(12, 6))
    todas_notas = pd.concat([df[col].dropna() for col in colunas])
    freq = todas_notas.value_counts().sort_index()
    
    colors = CONFIG_GRAFICOS['cores_barras'][:len(freq)]
    labels = [CONFIG_GRAFICOS['labels_notas'][i-1] for i in freq.index]
    
    bars = ax.bar(range(len(freq)), freq.values, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    ax.set_title(titulo or CONFIG_GRAFICOS['titulos'].get('servico_barras', 'Gráfico'), 
                fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Nota', fontsize=12, fontweight='bold')
    ax.set_ylabel('Frequência', fontsize=12, fontweight='bold')
    ax.set_xticks(range(len(freq)))
    ax.set_xticklabels(labels, rotation=0, fontweight='bold')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.1, f'{int(height)}', 
                ha='center', va='bottom', fontweight='bold', fontsize=11)
    plt.tight_layout()
    return fig

def grafico_pizza_frequencia(df, colunas, titulo=""):
    fig, ax = plt.subplots(figsize=(10, 8))
    todas_notas = pd.concat([df[col].dropna() for col in colunas])
    freq = todas_notas.value_counts().sort_index()
    
    colors = CONFIG_GRAFICOS['cores_pizza'][:len(freq)]
    labels = [CONFIG_GRAFICOS['labels_notas'][i-1] for i in freq.index]
    
    wedges, texts, autotexts = ax.pie(freq.values, labels=labels, colors=colors, 
                                    autopct='%1.1f%%', startangle=90,
                                    textprops={'fontsize': 12, 'fontweight': 'bold'})
    ax.set_title(titulo or CONFIG_GRAFICOS['titulos'].get('servico_pizza', 'Gráfico'), 
                fontsize=16, fontweight='bold', pad=20)
    
    for wedge in wedges:
        wedge.set_edgecolor('white')
        wedge.set_linewidth(2)
    plt.tight_layout()
    return fig

def calcular_indices(notas_filtradas):
    if notas_filtradas.empty:
        return pd.DataFrame()
    
    # Calcular médias
    colunas_funcionario = ["n1", "n2", "n3"]
    colunas_servico = ["n4", "n5"]
    
    indices = {}
    
    # Ranking de funcionários por média geral
    medias_func = notas_filtradas.groupby('nome')[colunas_funcionario].mean().mean(axis=1)
    indices['media_geral_func'] = medias_func.sort_values(ascending=False)
    
    # Taxa de excelência (nota 5)
    for col in colunas_funcionario:
        pct_excelencia = (notas_filtradas[col] == 5).mean() * 100
        indices[f'pct_excelencia_{col}'] = pct_excelencia
    
    # Média geral serviço
    media_servico = notas_filtradas[colunas_servico].mean().mean()
    indices['media_servico'] = media_servico
    
    # Taxa satisfação geral (média >= 4)
    pct_satisfacao = (notas_filtradas[colunas_funcionario].mean(axis=1) >= 4).mean() * 100
    indices['taxa_satisfacao'] = pct_satisfacao
    
    # Evolução temporal (últimos 7 dias vs período completo)
    if len(notas_filtradas) > 7:
        media_recente = notas_filtradas.tail(7)[colunas_funcionario].mean().mean()
        indices['evolucao_recente'] = media_recente - media_servico
    
    return indices

get_base64("fundoazulrev.PNG")
set_background("fundoazulrev.PNG")
add_logo_top_right("Logosenai.png")

init_db()
notas, obs, func = carregar_dados_completos()

if not notas.empty:
    notas["data_hora"] = pd.to_datetime(notas["data_hora"])
if not obs.empty:
    obs["data_hora"] = pd.to_datetime(obs["data_hora"])

st.title("🔍 Painel de Avaliações")

abas = st.tabs([
    "👥 Cadastro Funcionários",
    "📊 Avaliação do Serviço",
    "🏆 Desempenho Funcionários", 
    "💬 Observações",
    "📈 Índices de Análise"])

# ------------------------------------------------------------------
# ------------------------------------------------------------------
with abas[0]:
    st.header("Cadastro de Funcionários")
    
    # CARREGAR DADOS ATUALIZADOS SEMPRE NO INÍCIO DA ABA
    func_atualizados = carregar_dados_completos()[2]  # Pega só a tabela de funcionários
    
    # Criar pasta fotos se não existir
    if not os.path.exists("fotos"):
        os.makedirs("fotos")
    
    # SELEÇÃO DE MODO
    modo = st.radio("👇 Escolha a ação:", 
                   ["➕ Cadastrar Novo", "✏️ Editar Existente", "🗑️ Deletar", "👀 Visualizar"],
                   horizontal=True, key="modo_cadastro")
    
    col_nome, col_cargo = st.columns(2)
    with col_nome:
        nome = st.text_input("Nome Completo", key="n")
    with col_cargo:
        cargo = st.text_input("Cargo", key="c")
    
    foto = st.file_uploader("Foto (opcional)", 
                           type=["png", "jpg", "jpeg", "jfif"], 
                           key="foto_cad")
    
    foto_base64 = None
    if foto is not None:
        foto_base64 = base64.b64encode(foto.getvalue()).decode()
        st.success(f"Foto carregada: {foto.name}")
        st.image(foto, width=150, caption="Pré-visualização")
    
    # SELECTBOX PARA FUNCIONÁRIOS (só em Editar/Deletar)
    funcionario_sel = None
    if modo in ["✏️ Editar Existente", "🗑️ Deletar"] and not func_atualizados.empty:
        st.subheader("👥 Selecione o funcionário:")
        nomes_func = func_atualizados["nome"].tolist()
        funcionario_sel = st.selectbox("Funcionário:", nomes_func, key="func_sel")
        
        # MOSTRAR DADOS ATUAIS
        if funcionario_sel:
            func_dados = func_atualizados[func_atualizados["nome"] == funcionario_sel].iloc[0]
            st.info(f"**ID:** `{func_dados['id']}` | **Dados atuais:** Nome: *{func_dados['nome']}* | Cargo: *{func_dados['cargo']}*")
            if func_dados.get('foto'):
                st.image(f"data:image/png;base64,{func_dados['foto']}", width=150, caption="Foto atual")
    
    col1, col2 = st.columns(2)
    
    conn = conectar()  # Conexão sempre disponível
    
    # CADASTRAR
    if modo == "➕ Cadastrar Novo":
        with col1:
            if st.button("👤 Cadastrar Funcionário", type="primary", use_container_width=True, key="btn_cad"):
                if nome.strip():
                    data = {"nome": nome.strip(), "cargo": cargo or "", "foto": foto_base64}
                    conn.table('funcionarios').insert(data).execute()
                    st.success("✅ CADASTRADO!")
                    st.rerun()
    
    # EDITAR
    elif modo == "✏️ Editar Existente" and funcionario_sel:
        func_id = func_atualizados[func_atualizados["nome"] == funcionario_sel]["id"].iloc[0]
        with col1:
            if st.button("💾 Atualizar Dados", type="primary", use_container_width=True, key="btn_upd"):
                if nome.strip():
                    data_update = {
                        "nome": nome.strip(),
                        "cargo": cargo or "",
                        "foto": foto_base64 if foto_base64 else None
                    }
                    conn.table('funcionarios').update(data_update).eq('id', func_id).execute()
                    st.success("✅ ATUALIZADO!")
                    st.rerun()
    
    # DELETAR
    elif modo == "🗑️ Deletar" and funcionario_sel:
        func_id = func_atualizados[func_atualizados["nome"] == funcionario_sel]["id"].iloc[0]
        with col1:
            if st.button("🗑️ CONFIRMAR DELEÇÃO", type="primary", 
                        use_container_width=True, 
                        help="⚠️ Esta ação é irreversível!", 
                        key="btn_del"):
                conn.table('funcionarios').delete().eq('id', func_id).execute()
                st.success("✅ DELETADO!")
                st.rerun()
    
    # VISUALIZAR (SEMPRE ATUALIZADO)
    st.subheader("👥 Funcionários Cadastrados")
    if not func_atualizados.empty:
        st.dataframe(func_atualizados[["id", "nome", "cargo"]], use_container_width=True)
        st.caption(f"📊 Total: {len(func_atualizados)} funcionários")
    else:
        st.warning("❌ Nenhum funcionário cadastrado")

# ------------------------------------------------------------------
with abas[1]:
    st.header("Avaliação do Serviço")
    st.text("")
    st.subheader("Filtrar vizualização por período")
    col1, col2 = st.columns(2)
    data_inicio = col1.date_input("Data inicial", key="data_panorama_inicio")
    data_fim = col2.date_input("Data final", key="data_panorama_fim")
    
    if data_inicio and data_fim and not notas.empty:
        notas_servico = notas[(notas["data_hora"].dt.date >= data_inicio) & 
                             (notas["data_hora"].dt.date <= data_fim)].copy()
    else:
        notas_servico = notas.copy()
    
    if notas_servico.empty:
        st.warning("❌ Sem dados para análise")
    else:
        colunas_servico = ["n4", "n5"]
        st.subheader("🗄️ Avaliações Serviço")
        col_bd, col_dl = st.columns([4,1])
        with col_bd:
            st.metric("📊 Média Geral Serviço", f"{notas_servico[colunas_servico].mean().mean():.2f}/5")
            st.dataframe(notas_servico[["id", "nome", "n4", "n5", "data_hora"]], use_container_width=True)
        with col_dl:
            baixar_csv(notas_servico[["id", "nome", "n4", "n5", "data_hora"]], "servico_completo.csv")
        
        col1, col2 = st.columns(2)
        with col1:
            fig_barras = grafico_barras_frequencia(notas_servico, colunas_servico, 
                                                 CONFIG_GRAFICOS['titulos']['servico_barras'])
            st.pyplot(fig_barras)
        with col2:
            fig_pizza = grafico_pizza_frequencia(notas_servico, colunas_servico, 
                                               CONFIG_GRAFICOS['titulos']['servico_pizza'])
            st.pyplot(fig_pizza)

# ------------------------------------------------------------------
with abas[2]:
    st.header("🏆 Desempenho Funcionários")
    st.text("")
    st.subheader("Filtrar vizualização por período")
    col1, col2 = st.columns(2)
    data_inicio = col1.date_input("Data inicial", key="data_func_inicio")
    data_fim = col2.date_input("Data final", key="data_func_fim")
    
    if data_inicio and data_fim and not notas.empty:
        notas_filtradas = notas[(notas["data_hora"].dt.date >= data_inicio) & 
                               (notas["data_hora"].dt.date <= data_fim)].copy()
    else:
        notas_filtradas = notas.copy()
    
    if notas_filtradas.empty:
        st.warning("❌ Sem dados para análise")
    else:
        # FILTRO FUNCIONÁRIO
        col_filt1, col_filt2 = st.columns([1,2])
        funcionario_sel = col_filt2.selectbox("Funcionário:", 
            ["TODOS"] + sorted(notas_filtradas["nome"].dropna().unique().tolist()))
        
        dados_view = notas_filtradas.copy()
        if funcionario_sel != "TODOS":
            dados_view = dados_view[dados_view["nome"] == funcionario_sel]

        colunas_funcionario = ["n1", "n2", "n3"]
        
        st.subheader("🗄️ Avaliações Funcionário")
        col_bd, col_dl = st.columns([4,1])
        with col_bd:
            st.metric("⭐ Média Funcionário", f"{dados_view[colunas_funcionario].mean().mean():.2f}/5")
            st.dataframe(dados_view[["id", "nome", "n1", "n2", "n3", "data_hora"]], use_container_width=True)
        with col_dl:
            baixar_csv(dados_view[["id", "nome", "n1", "n2", "n3", "data_hora"]], "funcionario_completo.csv")
        
        col1, col2 = st.columns(2)
        with col1:
            fig_barras = grafico_barras_frequencia(dados_view, colunas_funcionario, 
                                                 f"{CONFIG_GRAFICOS['titulos']['func_barras']} - {funcionario_sel}")
            st.pyplot(fig_barras)
        with col2:
            fig_pizza = grafico_pizza_frequencia(dados_view, colunas_funcionario, 
                                               f"{CONFIG_GRAFICOS['titulos']['func_pizza']} - {funcionario_sel}")
            st.pyplot(fig_pizza)

# ------------------------------------------------------------------
with abas[3]:
    st.header("💬 Observações")
    st.text("")
    st.subheader("Filtrar vizualização por período")
    col1, col2 = st.columns(2)
    data_inicio = col1.date_input("Data inicial", key="data_obs_inicio")
    data_fim = col2.date_input("Data final", key="data_obs_fim")
    
    if data_inicio and data_fim and not obs.empty:
        obs_filtradas = obs[(obs["data_hora"].dt.date >= data_inicio) & 
                           (obs["data_hora"].dt.date <= data_fim)].copy()
    else:
        obs_filtradas = obs.copy()
    
    if obs_filtradas.empty:
        st.warning("Sem observações")
    else:
        col_bd, col_dl = st.columns([4,1])
        with col_bd:
            st.dataframe(obs_filtradas, use_container_width=True)
        with col_dl:
            baixar_csv(obs_filtradas, "observacoes_completo.csv")
        
        st.subheader("📝 Detalhes")
        obs_filtradas = obs_filtradas.sort_values('data_hora', ascending=False)
        for _, row in obs_filtradas.iterrows():
            st.markdown(f"""
            <div style="background-color: rgba(255,255,255,0.9); padding:20px; border-radius:15px; margin:10px 0; border-left:5px solid #2196F3;">
                <h4>👤 <b></b></h4>
                <small>📅 {row['data_hora'].strftime('%d/%m/%Y %H:%M')}</small>
                <p style="margin-top:10px; font-size:16px;">{row['obs']}</p>
            </div>
            """, unsafe_allow_html=True)

# ------------------------------------------------------------------
with abas[4]:
    st.header("📈 Índices de Análise")
    st.text("")
    
    st.subheader("Filtrar análise por período")
    col1, col2 = st.columns(2)
    data_inicio_idx = col1.date_input("Data inicial", key="data_idx_inicio")
    data_fim_idx = col2.date_input("Data final", key="data_idx_fim")
    
    if data_inicio_idx and data_fim_idx and not notas.empty:
        notas_analise = notas[(notas["data_hora"].dt.date >= data_inicio_idx) & 
                             (notas["data_hora"].dt.date <= data_fim_idx)].copy()
    else:
        notas_analise = notas.copy()
    
    if notas_analise.empty:
        st.warning("❌ Sem dados para análise de índices")
    else:
        indices = calcular_indices(notas_analise)
        
        # KPIs Principais
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("⭐ Média Geral", f"{indices.get('media_geral_func', 0).mean():.2f}/5")
        with col2:
            st.metric("🎯 Taxa Satisfação", f"{indices.get('taxa_satisfacao', 0):.1f}%")
        with col3:
            st.metric("🏆 Top Performer", 
                     f"{indices['media_geral_func'].index[0] if len(indices['media_geral_func']) > 0 else 'N/A'}")
        with col4:
            st.metric("📈 Evolução Recente", 
                     f"{indices.get('evolucao_recente', 0):+.2f}")
        
        # Tabela de Ranking Funcionários
        st.subheader("🏅 Ranking de Desempenho")
        df_ranking = pd.DataFrame({
            'Funcionário': indices['media_geral_func'].index,
            'Média Geral': indices['media_geral_func'].values.round(2),
            'Taxa Excelência (%)': [
                ((notas_analise[notas_analise['nome'] == func]['n1'] == 5).mean() * 100 +
                 (notas_analise[notas_analise['nome'] == func]['n2'] == 5).mean() * 100 +
                 (notas_analise[notas_analise['nome'] == func]['n3'] == 5).mean() * 100) / 3
                for func in indices['media_geral_func'].index
            ]
        }).round(2)
        
        st.dataframe(df_ranking.head(10), use_container_width=True)
        
        # Gráfico Ranking
        fig_ranking, ax = plt.subplots(figsize=(12, 6))
        top_10 = df_ranking.head(10)
        colors = CONFIG_GRAFICOS['cores_ranking'][:len(top_10)] # NOVO: usa cores personalizadas
        bars = ax.barh(range(len(top_10)), top_10['Média Geral'], color=colors, alpha=0.8)
        ax.set_yticks(range(len(top_10)))
        ax.set_yticklabels(top_10['Funcionário'])
        ax.set_xlabel('Média Geral (0-5)')
        ax.set_title(CONFIG_GRAFICOS['titulos']['ranking'], fontweight='bold', fontsize=16) # NOVO: título personalizado
        ax.grid(axis='x', alpha=0.3)

        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax.text(width + 0.01, bar.get_y() + bar.get_height()/2, 
                   f'{width:.2f}', va='center', fontweight='bold')
        
        st.pyplot(fig_ranking)
        
        st.subheader("📊 Detalhes dos Índices")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("📈 Média Serviço", f"{indices.get('media_servico', 0):.2f}/5")
            st.metric("⭐ % Notas 5 (N1)", f"{(notas_analise['n1'] == 5).mean()*100:.1f}%")
            st.metric("⭐ % Notas 5 (N2)", f"{(notas_analise['n2'] == 5).mean()*100:.1f}%")
            st.metric("⭐ % Notas 5 (N3)", f"{(notas_analise['n3'] == 5).mean()*100:.1f}%")
        
        with col2:
            st.metric("🎯 Satisfação Geral", f"{indices.get('taxa_satisfacao', 0):.1f}%")
            st.metric("📊 Total Avaliações", len(notas_analise))
            st.metric("👥 Funcionários Avaliados", len(indices['media_geral_func']))
            st.metric("📅 Período Analisado", 
                     f"{notas_analise['data_hora'].min().strftime('%d/%m')}-{notas_analise['data_hora'].max().strftime('%d/%m')}")
        
        # Baixar relatório completo
        st.download_button(
            label="📥 Baixar Relatório Completo de Índices",
            data=df_ranking.to_csv(index=False),
            file_name=f"relatorio_indices_{data_inicio_idx or 'completo'}_{data_fim_idx or 'completo'}.csv",
            mime='text/csv')
