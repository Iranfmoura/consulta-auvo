import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Raio-X Omie", layout="wide")
st.title("🩻 Raio-X Omie: Onde estão os produtos?")

# --- Carregar Chaves ---
if "omie" in st.secrets:
    app_key = st.secrets["omie"]["app_key"]
    app_secret = st.secrets["omie"]["app_secret"]
    st.success("🔒 Chaves carregadas.")
else:
    app_key = st.sidebar.text_input("App Key", type="password").strip()
    app_secret = st.sidebar.text_input("App Secret", type="password").strip()

if st.button("Iniciar Varredura Profunda"):
    if not app_key or not app_secret:
        st.error("Preciso das chaves.")
    else:
        url_prod = "https://app.omie.com.br/api/v1/geral/produtos/"
        url_fam = "https://app.omie.com.br/api/v1/geral/familias/"
        
        # --- TESTE 1: As Famílias de Produtos existem? ---
        # Se isso retornar 0, a chave está conectada em uma empresa vazia.
        st.subheader("1. Teste de Famílias (Categorias)")
        try:
            pl_fam = {
                "call": "ListarFamiliasProdutos",
                "app_key": app_key, 
                "app_secret": app_secret,
                "param": [{"pagina": 1, "registros_por_pagina": 20}]
            }
            resp_fam = requests.post(url_fam, json=pl_fam)
            if resp_fam.status_code == 200:
                d_fam = resp_fam.json()
                total_fam = d_fam.get("total_de_registros", 0)
                lista_fam = d_fam.get("fam_cadastro", [])
                
                if total_fam > 0:
                    st.success(f"✅ Sucesso: Encontrei {total_fam} famílias de produtos.")
                    st.write(f"Exemplo: {lista_fam[0].get('nomeFam')}")
                else:
                    st.error("❌ O Omie diz que NÃO existem Famílias cadastradas nesta conta.")
                    st.info("💡 Dica: Se no site tem famílias, então essa CHAVE API é de outra filial/empresa.")
            else:
                st.error(f"Erro na conexão de famílias: {resp_fam.status_code}")
        except Exception as e:
            st.error(f"Erro técnico teste 1: {e}")

        # --- TESTE 2: Busca Genérica (Sem filtro de API/Manual) ---
        st.subheader("2. Teste de Produtos (Sem Filtros)")
        try:
            pl_gen = {
                "call": "ListarProdutos",
                "app_key": app_key, 
                "app_secret": app_secret,
                "param": [{
                    "pagina": 1, 
                    "registros_por_pagina": 20,
                    "apenas_importado_api": "N", # Tenta manual padrão
                    "exibir_inativos": "S"       # O PULO DO GATO: Mostra inativos
                }]
            }
            resp_gen = requests.post(url_prod, json=pl_gen)
            data_gen = resp_gen.json()
            lista_gen = data_gen.get("produto_servico_cadastro", [])
            
            if lista_gen:
                st.success(f"✅ ACHEI! Retornou {len(lista_gen)} produtos nesta página.")
                
                # Mostra os 3 primeiros para conferência
                amostra = []
                for p in lista_gen[:5]:
                    amostra.append({
                        "Nome": p.get("descricao"), 
                        "Inativo?": p.get("inativo"),
                        "Origem": "API" if p.get("importado_api") == "S" else "Manual"
                    })
                st.table(pd.DataFrame(amostra))
            else:
                st.warning("⚠️ Ainda retornou lista vazia, mesmo pedindo inativos.")
                st.json(data_gen) # Mostra o JSON cru para vermos o erro
                
        except Exception as e:
            st.error(f"Erro técnico teste 2: {e}")
