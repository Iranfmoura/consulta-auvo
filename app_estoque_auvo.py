import streamlit as st
import requests
import pandas as pd
import json
import os

# --- Funções de Memória ---
ARQUIVO_CONFIG = "config_auvo.json"

def carregar_chaves():
    # 1. Tenta ler dos Segredos da Nuvem (Streamlit Cloud)
    if "auvo" in st.secrets:
        return {
            "api_key": st.secrets["auvo"]["api_key"],
            "api_token": st.secrets["auvo"]["api_token"],
            "endpoint": st.secrets["auvo"].get("endpoint", "products")
        }
    
    # 2. Se não achar na nuvem, tenta ler do arquivo local (seu PC)
    if os.path.exists(ARQUIVO_CONFIG):
        try:
            with open(ARQUIVO_CONFIG, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def salvar_chaves(key, token, endpoint_pref):
    dados = {
        "api_key": key,
        "api_token": token,
        "endpoint": endpoint_pref
    }
    with open(ARQUIVO_CONFIG, "w") as f:
        json.dump(dados, f)

# --- Configuração da Página ---
st.set_page_config(page_title="Consulta Auvo", layout="wide")
st.title("📦 Consulta Auvo (Ativos e Estoque)")

memoria = carregar_chaves()
key_salva = memoria.get("api_key", "")
token_salvo = memoria.get("api_token", "")
endpoint_salvo = memoria.get("endpoint", "equipments")

# --- Barra Lateral ---
# --- Barra Lateral ---
with st.sidebar:
    st.header("Configuração")
    
    # --- LOGICA DE SEGURANÇA ---
    # Se existirem chaves nos 'Secrets' (Nuvem), usamos elas e escondemos os campos.
    if "auvo" in st.secrets:
        api_key = st.secrets["auvo"]["api_key"]
        api_token = st.secrets["auvo"]["api_token"]
        st.success("🔒 Acesso Seguro Ativo")
        st.caption("As credenciais estão ocultas e protegidas.")
    else:
        # Se NÃO tiver secrets (uso local no seu PC), mostra os campos para digitar
        api_key = st.text_input("API Key (Chave)", value=key_salva, type="password").strip()
        api_token = st.text_input("API Token", value=token_salvo, type="password").strip()
    
    st.markdown("---")
    
    # O resto continua igual (Seletor de Tipo e Checkbox)
    opcoes_validas = ["equipments", "products", "materials"]
    
    # Tenta definir o valor padrão
    index_sel = 0
    # Se tiver secrets, tenta pegar a preferência de lá, senão usa a memória local
    pref_endpoint = st.secrets["auvo"].get("endpoint") if "auvo" in st.secrets else endpoint_salvo
    
    if pref_endpoint in opcoes_validas:
        index_sel = opcoes_validas.index(pref_endpoint)

    endpoint = st.selectbox("Tipo de Busca", opcoes_validas, index=index_sel)
    
    # Só mostra opção de salvar se estiver no modo manual (local)
    if "auvo" not in st.secrets:
        salvar_auto = st.checkbox("Memorizar dados", value=True)
    else:
        salvar_auto = False # Na nuvem não salvamos localmente

# --- Função de Login ---
def fazer_login_auvo(key, token):
    url_login = "https://api.auvo.com.br/v2/login"
    payload = {"apiKey": key, "apiToken": token}
    try:
        response = requests.post(url_login, json=payload)
        if response.status_code == 200:
            resultado = response.json().get('result', {})
            if isinstance(resultado, dict):
                return resultado.get('accessToken')
            return None
        else:
            st.error(f"Falha no Login ({response.status_code}): {response.text}")
            return None
    except Exception as e:
        st.error(f"Erro de conexão no login: {e}")
        return None

# --- Área Principal ---
st.subheader(f"Consultando: {endpoint.upper()}")
termo = st.text_input("Filtrar por nome (opcional)")

if st.button("Consultar"):
    if not api_key or not api_token:
        st.warning("Preencha a API Key e o Token na barra lateral.")
    else:
        if salvar_auto:
            salvar_chaves(api_key, api_token, endpoint)

        with st.spinner("Autenticando e buscando..."):
            access_token = fazer_login_auvo(api_key, api_token)
        
        if access_token:
            url_consulta = f"https://api.auvo.com.br/v2/{endpoint}"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            # Mandamos o search para a API tentar filtrar
            params = {"search": termo} 

            try:
                response = requests.get(url_consulta, headers=headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Estruturas possíveis
                    itens = []
                    if 'result' in data and isinstance(data['result'], dict) and 'entityList' in data['result']:
                        itens = data['result']['entityList']
                    elif 'result' in data and isinstance(data['result'], list):
                        itens = data['result']
                    elif isinstance(data, list):
                        itens = data

                    if isinstance(itens, list) and len(itens) > 0:
                        lista_final = []
                        termo_lower = termo.lower().strip() if termo else ""

                        for item in itens:
                            nome = item.get('name') or item.get('description') or ""
                            descricao = item.get('description') or ""
                            identificador = item.get('identifier') or ""
                            
                            # --- FILTRO DO PYTHON (GARANTIA) ---
                            # Só adiciona na lista final se:
                            # 1. O usuário não digitou nada (mostra tudo)
                            # 2. OU o texto digitado está no Nome, Descrição ou Identificador
                            texto_completo = f"{nome} {descricao} {identificador}".lower()
                            
                            if not termo_lower or termo_lower in texto_completo:
                                dados_item = {
                                    "ID": item.get('id'),
                                    "Nome": nome,
                                    "Identificador/Série": identificador,
                                    "Descrição": descricao,
                                }
                                
                                if 'stockQuantity' in item:
                                    dados_item["Estoque"] = item['stockQuantity']
                                elif 'amount' in item:
                                    dados_item["Estoque"] = item['amount']
                                    
                                lista_final.append(dados_item)
                        
                        # Exibe o resultado filtrado
                        if lista_final:
                            df = pd.DataFrame(lista_final)
                            st.success(f"{len(df)} registros encontrados com '{termo}'.")
                            st.dataframe(df, use_container_width=True)
                        else:
                            st.warning(f"A API retornou dados, mas nenhum continha a palavra '{termo}'.")
                    else:
                        st.info("Nenhum item encontrado no servidor.")
                else:
                    st.error(f"Erro na consulta ({response.status_code}): {response.text}")

            except Exception as e:

                st.error(f"Ocorreu um erro técnico: {e}")

