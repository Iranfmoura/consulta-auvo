import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Forense Omie", layout="wide")
st.title("🔬 Forense do Produto 946")

if "omie" in st.secrets:
    app_key = st.secrets["omie"]["app_key"]
    app_secret = st.secrets["omie"]["app_secret"]
    st.success("🔒 Chaves carregadas.")
else:
    app_key = st.sidebar.text_input("App Key", type="password").strip()
    app_secret = st.sidebar.text_input("App Secret", type="password").strip()

if st.button("Analisar Produto 946"):
    if not app_key:
        st.warning("Faltam as chaves.")
    else:
        url = "https://app.omie.com.br/api/v1/geral/produtos/"
        
        payload = {
            "call": "ConsultarProduto",
            "app_key": app_key,
            "app_secret": app_secret,
            "param": [{"codigo": "946"}] # Código que sabemos que existe
        }

        try:
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                p = response.json()
                
                st.subheader("📋 Relatório Técnico")
                
                # 1. VERIFICAÇÃO DE STATUS (O Suspeito Nº 1)
                is_inativo = p.get("inativo") == "S"
                if is_inativo:
                    st.error("🚨 VEREDITO: O PRODUTO ESTÁ INATIVO!")
                    st.markdown("""
                    **Explicação:** A API do Omie **esconde automaticamente** produtos inativos das listagens de busca. 
                    É por isso que a busca por nome retorna vazio, mas a busca por código funciona.
                    **Solução:** Reative o produto no painel do Omie para ele aparecer na busca.
                    """)
                else:
                    st.success("✅ Status: ATIVO (Não é isso que está bloqueando)")

                # 2. VERIFICAÇÃO DE ORIGEM API (O Suspeito Nº 2)
                importado = p.get("importado_api")
                st.info(f"ℹ️ Flag 'importado_api': '{importado}'")
                
                if importado == "N":
                    st.write("O produto é considerado **Manual**.")
                elif importado == "S":
                    st.write("O produto é considerado **Importado via API**.")
                else:
                    st.warning("O produto está num limbo (nem S, nem N).")

                # 3. DADOS GERAIS
                st.json({
                    "Descrição": p.get("descricao"),
                    "Código": p.get("codigo"),
                    "Inativo?": p.get("inativo"),
                    "Importado API?": p.get("importado_api"),
                    "Bloqueado?": p.get("bloqueado")
                })
                
            else:
                st.error(f"Erro ao consultar: {response.text}")

        except Exception as e:
            st.error(f"Erro técnico: {e}")
