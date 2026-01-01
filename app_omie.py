import streamlit as st
import requests
import pandas as pd
import json

# --- Configuração da Página ---
st.set_page_config(page_title="Consulta Omie", layout="wide")
st.title("🏭 Consulta Produtos - Omie")

# --- Carregar Chaves (Secrets ou Manual) ---
if "omie" in st.secrets:
    app_key = st.secrets["omie"]["app_key"]
    app_secret = st.secrets["omie"]["app_secret"]
    st.success("🔒 Chaves Omie Carregadas")
    modo_seguro = True
else:
    st.sidebar.header("Credenciais Omie")
    app_key = st.sidebar.text_input("App Key", type="password").strip()
    app_secret = st.sidebar.text_input("App Secret", type="password").strip()
    st.warning("⚠️ Modo Manual")
    modo_seguro = False

# --- Área de Busca ---
termo = st.text_input("Nome do Produto no Omie", placeholder="Ex: Tubo")

if st.button("Buscar no Omie"):
    if not app_key or not app_secret:
        st.error("Preencha a App Key e o App Secret.")
    else:
        # URL Oficial
        url = "https://app.omie.com.br/api/v1/geral/produtos/"
        
        # CORREÇÃO: Removemos o filtro que dava erro e aumentamos o limite para 500
        payload = {
            "call": "ListarProdutos",
            "app_key": app_key,
            "app_secret": app_secret,
            "param": [
                {
                    "pagina": 1,
                    "registros_por_pagina": 500, # Traz um lote grande para pesquisar
                    "apenas_importado_api": "N"
                }
            ]
        }

        try:
            with st.spinner("Baixando lista de produtos do Omie..."):
                response = requests.post(url, json=payload)

            if response.status_code == 200:
                data = response.json()
                
                # Pega a lista total de produtos retornada
                lista_bruta = data.get("produto_servico_cadastro", [])

                if lista_bruta:
                    # --- FILTRAGEM INTELIGENTE NO PYTHON ---
                    # O Omie não filtra, então nós filtramos aqui:
                    produtos_encontrados = []
                    termo_lower = termo.lower() # Converter para minúsculo para facilitar

                    for item in lista_bruta:
                        descricao = item.get("descricao", "").lower()
                        codigo = str(item.get("codigo", "")).lower()
                        
                        # Se o termo digitado estiver na Descrição OU no Código
                        if termo_lower in descricao or termo_lower in codigo:
                            produtos_encontrados.append({
                                "Código": item.get("codigo"),
                                "Descrição": item.get("descricao"),
                                "Preço": f"R$ {item.get('valor_unitario', 0)}",
                                "NCM": item.get("ncm"),
                                "Unidade": item.get("unidade"),
                                "ID Omie": item.get("codigo_produto")
                            })
                    
                    # Exibe o resultado
                    if produtos_encontrados:
                        df = pd.DataFrame(produtos_encontrados)
                        st.success(f"{len(df)} produtos encontrados (na primeira página de 500 itens).")
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.warning(f"Baixei 500 produtos, mas nenhum continha a palavra '{termo}'.")
                else:
                    st.info("O Omie não retornou nenhum produto cadastrado.")
            
            elif response.status_code == 500:
                erro_msg = response.json().get("faultstring", "Erro desconhecido")
                st.error(f"Erro do Omie: {erro_msg}")
            else:
                st.error(f"Erro na conexão ({response.status_code}): {response.text}")

        except Exception as e:
            st.error(f"Erro técnico: {e}")

st.markdown("---")
st.caption("Conectado via API v1 (ListarProdutos - Lote de 500)")
