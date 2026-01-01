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
    st.success("🔒 Chaves Omie Carregadas (Modo Seguro)")
    modo_seguro = True
else:
    st.sidebar.header("Credenciais Omie")
    app_key = st.sidebar.text_input("App Key", type="password").strip()
    app_secret = st.sidebar.text_input("App Secret", type="password").strip()
    st.warning("⚠️ Modo Manual (Configure os Secrets para maior segurança)")
    modo_seguro = False

# --- Área de Busca ---
termo = st.text_input("Nome do Produto no Omie", placeholder="Ex: Parafuso")

if st.button("Buscar no Omie"):
    if not app_key or not app_secret:
        st.error("Preencha a App Key e o App Secret.")
    else:
        # URL Oficial para Listagem de Produtos
        url = "https://app.omie.com.br/api/v1/geral/produtos/"
        
        # O Omie exige que os parâmetros vão dentro de uma lista "param"
        payload = {
            "call": "ListarProdutos",
            "app_key": app_key,
            "app_secret": app_secret,
            "param": [
                {
                    "pagina": 1,
                    "registros_por_pagina": 50, # Traz até 50 itens
                    "apenas_importado_api": "N",
                    "filtrar_por_descricao": termo # Aqui entra o seu filtro
                }
            ]
        }

        try:
            with st.spinner("Consultando Omie..."):
                # O Omie é sempre POST, mesmo para buscar dados
                response = requests.post(url, json=payload)

            if response.status_code == 200:
                data = response.json()
                
                # O Omie retorna a lista dentro de 'produto_servico_cadastro'
                lista_produtos = data.get("produto_servico_cadastro", [])

                if lista_produtos:
                    dados_formatados = []
                    for item in lista_produtos:
                        dados_formatados.append({
                            "Código": item.get("codigo"),
                            "Descrição": item.get("descricao"),
                            "Preço Unitário": f"R$ {item.get('valor_unitario', 0)}",
                            "NCM": item.get("ncm"),
                            "Família": item.get("descricao_familia", "-"),
                            "ID Omie": item.get("codigo_produto")
                        })
                    
                    df = pd.DataFrame(dados_formatados)
                    st.success(f"{len(df)} produtos encontrados.")
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("Nenhum produto encontrado com esse nome.")
            
            elif response.status_code == 500:
                # Erro comum no Omie quando não acha nada ou erro de sintaxe
                erro_msg = response.json().get("faultstring", "Erro desconhecido")
                if "ERROR: NO-RECORDS-FOUND" in str(response.text):
                     st.warning("Nenhum registro encontrado.")
                else:
                    st.error(f"Erro do Omie: {erro_msg}")
            else:
                st.error(f"Erro na conexão ({response.status_code}): {response.text}")

        except Exception as e:
            st.error(f"Erro técnico: {e}")

st.markdown("---")
st.caption("Conectado via API v1 (Geral/Produtos)")
