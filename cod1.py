import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import base64
import os

st.set_page_config(page_title="Pesquisa de Satisfação", layout="centered")

# Fotos
if not os.path.exists("fotos"):
    os.makedirs("fotos")

# Supabase
SUPABASE_URL = "https://jmxkzrzevnchfbbzfpun.supabase.co"     
SUPABASE_KEY = "sb_publishable_ggxYOSD-3KmSSiWYDrcshQ_T53QnyJz"

def conectar():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def init_db():
    pass

def carregar_funcionarios():
    conn = conectar()
    try:
        response = conn.table('funcionarios').select("*").execute()
        data = response.data
        if data:
            df = pd.DataFrame(data)
            st.sidebar.success(f"✅ {len(df)} funcionário(s)")
            return df
        st.sidebar.info("ℹ️ Cadastre funcionários no Painel Admin")
        return pd.DataFrame(columns=['id', 'nome', 'cargo', 'foto'])
    except Exception as e:
        st.sidebar.error(f"Erro: {str(e)[:50]}")
        return pd.DataFrame(columns=['id', 'nome', 'cargo', 'foto'])

def salvar_avaliacao(funcionario_id, nota1, nota2, nota3, nota4, nota5, obs):
    conn = conectar()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    data_notas = {
        "funcionario_id": int(funcionario_id),
        "n1": nota1, "n2": nota2, "n3": nota3,
        "n4": nota4, "n5": nota5,
        "data_hora": now
    }
    conn.table('notas').insert(data_notas).execute()

    if obs:
        data_obs = {
            "funcionario_id": int(funcionario_id),
            "obs": obs,
            "data_hora": now
        }
        conn.table('observacoes').insert(data_obs).execute()

    st.success("Avaliação enviada!")
    st.rerun()  

def get_base64(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return None

def set_background(png_file):
    try:
        bin_str = get_base64(png_file)
        if bin_str:
            page_bg_img = '''
            <style>
            .stApp {
            background-image: url("data:image/png;base64,%s");
            background-size: cover;
            background-repeat: no-repeat;
            background-position: center;
            background-attachment: fixed;
            }
            </style>
            ''' % bin_str
            st.markdown(page_bg_img, unsafe_allow_html=True)
    except:
        pass
   
def add_logo_top_right(image_path):
    try:
        img_base64 = get_base64(image_path)
        if img_base64:
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
    except:
        pass

set_background("fundoazul.png")
add_logo_top_right("Logosenai.png")

init_db()

st.title("Pesquisa de Satisfação")

funcionarios = carregar_funcionarios()
selecionado = "Selecione"
func = None

if not funcionarios.empty:
    nomes = ["Selecione"] + funcionarios["nome"].fillna("Sem nome").tolist()
    selecionado = st.selectbox("👤 Funcionário:", nomes)
    
    if selecionado != "Selecione":
        func_filtrado = funcionarios[funcionarios["nome"] == selecionado]
        if not func_filtrado.empty:
            func = func_filtrado.iloc[0]

# EXATA LÓGICA DO CÓDIGO QUE FUNCIONAVA!
avatar_padrao = "https://identidade.senai.br/authenticationendpoint/extensions/layouts/custom/assets/img/nai.png"

if selecionado == "Selecione":
    # Avatar padrão QUADRADO usando st.image() como no código que funcionava
    st.image(avatar_padrao, width=150)
else:
    # Funcionário selecionado
    if func["foto"] and os.path.exists(func["foto"]):
        # Foto do funcionário REDONDA usando get_base64() como no código que funcionava
        img_base64 = get_base64(func["foto"])
        st.markdown(
            f"""
            <img src="data:image/png;base64,{img_base64}" width="150" style="border-radius:50%">
            """,
            unsafe_allow_html=True
        )
    else:
        # Sem foto, avatar padrão QUADRADO
        st.image(avatar_padrao, width=150)

# Formulário
st.markdown("""
<style>
div[data-testid="stForm"] {
    background-color: rgba(255, 255, 255, 0.9);
    padding: 25px;
    border-radius: 20px;
    box-shadow: 0 8px 25px rgba(0,67,130,0.3);
}
</style>
""", unsafe_allow_html=True)

with st.form("avaliacoes", clear_on_submit=True):
    if selecionado != "Selecione":
        st.title(f"Avaliação do Funcionário: {selecionado}")
    else:
        st.title("Avaliação do Funcionário")
    st.write(f"Por favor avalie o atendimento do funcionário com uma nota de 1 a 5.")
    st.subheader("Cordialidade e Empatia")
    st.write("O funcionário foi educado e demonstrou interesse em resolver a sua questão?")
    n1 = st.slider("",1,5, key="1")

    st.subheader("Clareza na comunicação")
    st.write("As informações foram passadas de forma clara e obejetiva?")
    n2 = st.slider("",1,5, key="2")

    st.subheader("Agilidade")
    st.write("O tempo de espera no atendimento e a rapidez do funcionário foram satisfatórios?")
    n3 = st.slider("",1,5 ,key="3")

    st.title("Avaliação do Serviço")
    st.write("Por favor a avalie o nosso serviço com uma nota de 1 a 5.")
    st.subheader("Eficácia")
    st.write("Seu problema ou dúvida foi totalmente resolvido?")
    n4 = st.slider("",1,5, key="4")

    st.subheader("Foi fácil realizar o seu procedimento ou solicitação?")
    st.write("O tempo de espera no atendimento e a rapidez do funcionário foram satisfatórios?")
    n5 = st.slider("",1,5, key="5")

    st.header("Queremos ouvir você!")
    st.write("Por favor deixe sua sugestão ou comentário")
    obs = st.text_area("Deixe sua opinião:", height=80, key="obs")
    
    col_esq, col_btn = st.columns([3, 1])
    with col_esq:
        st.markdown("---")
    with col_btn:
        enviar = st.form_submit_button("Enviar Avaliação", type="primary", use_container_width=True)
    
    if enviar:
        if selecionado == "Selecione" or funcionarios.empty or func is None:
            st.error("**Selecione um funcionário válido!**")
        else:
            funcionario_id = func["id"]
            salvar_avaliacao(funcionario_id, n1, n2, n3, n4, n5, obs)

st.markdown("---")
st.markdown("*O SENAI agradece a sua colaboração*")