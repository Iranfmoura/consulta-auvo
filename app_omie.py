import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Teste Simplificado Omie", layout="wide")
st.title("🔍 Teste Final: Método Simplificado")

if "omie" in st.secrets:
    app_key = st.secrets["omie"]["app_key"]
    app_secret = st.secrets["omie"]["app_secret"]
    st.success("🔒 Chaves carregadas.")
else:
    app_key = st.sidebar.text_input("App Key", type="password").strip()
    app_secret = st.sidebar.text_input("App Secret", type="password").strip()

if st.button("Buscar Produtos (Modo Resumido)"):
    if not app_key or not app_secret:
        st.error("Preciso das chaves.")
    else:
        # URL Geral
        url_prod = "https://app.omie.com.br/api/v1/geral/produtos/"
        url_serv = "https://app.omie.com.br/api/v1/servicos/servico/"
        
        # --- TENTATIVA 1: PRODUTOS RESUMIDOS ---
        # Esse método é "blindado". Ele costuma funcionar quando o ListarProdutos falha.
        st.subheader("1. Buscando Produtos (Modo Resumido)")
        try:
            payload_res = {
                "call": "ListarProdutosResumido",
                "app_key": app_key, 
                "app_secret": app_secret,
                "param": [{
                    "pagina": 1, 
                    "registros_por_pagina": 20,
                    "apenas_importado_api": "N" # Tenta manual primeiro
                }]
            }
            
            resp = requests.post(url_prod, json=payload_res)
            
            if resp.status_code == 200:
                data = resp.json()
                lista = data.get("produto_servico_resumido", [])
                if lista:
                    st.success(f"✅ SUCESSO! Encontrei {len(lista)} produtos resumidos.")
                    st.dataframe(pd.DataFrame(lista))
                else:
                    st.warning("⚠️ O modo resumido retornou lista vazia para produtos manuais.")
                    
                    # Tenta Importados se o manual falhou
                    st.write("Tentando buscar importados...")
                    payload_res["param"][0]["apenas_importado_api"] = "S"
                    resp2 = requests.post(url_prod, json=payload_res)
                    lista2 = resp2.json().get("produto_servico_resumido", [])
                    if lista2:
                         st.success(f"✅ SUCESSO! Encontrei {len(lista2)} produtos importados.")
                         st.dataframe(pd.DataFrame(lista2))
                    else:
                         st.error("❌ Nada nos importados também.")
            else:
                st.error(f"Erro no modo resumido: {resp.status_code}")
                st.write(resp.text)
                
        except Exception as e:
            st.error(f"Erro técnico: {e}")

        st.markdown("---")

        # --- TENTATIVA 2: SERVIÇOS ---
        # Vai que o "Tubo" está cadastrado como serviço...
        st.subheader("2. Verificando Serviços")
        try:
            payload_serv = {
                "call": "ListarCadastroServico",
                "app_key": app_key, 
                "app_secret": app_secret,
                "param": [{"pagina": 1, "registros_por_pagina": 20}]
            }
            resp_s = requests.post(url_serv, json=payload_serv)
            data_s = resp_s.json()
            lista_s = data_s.get("cadastros_servicos", [])
            
            if lista_s:
                st.info(f"ℹ️ Encontrei {len(lista_s)} serviços cadastrados.")
                st.write(f"Exemplo: {lista_s[0].get('descricao')}")
            else:
                st.write("Nenhum serviço encontrado.")
                
        except Exception as e:
            st.write(f"Erro ao ler serviços (pode ser normal se não usar): {e}")
