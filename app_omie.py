import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Teste Unitário Omie", layout="wide")
st.title("🎯 Busca de Precisão (Código Exato)")

if "omie" in st.secrets:
    app_key = st.secrets["omie"]["app_key"]
    app_secret = st.secrets["omie"]["app_secret"]
    st.success("🔒 Chaves carregadas.")
else:
    app_key = st.sidebar.text_input("App Key", type="password").strip()
    app_secret = st.sidebar.text_input("App Secret", type="password").strip()

# Entrada do Código
codigo_alvo = st.text_input("Digite o CÓDIGO de um produto que existe (ex: 001, TUB-X):")

if st.button("Consultar Este Produto"):
    if not app_key or not codigo_alvo:
        st.warning("Preencha o código do produto para testar.")
    else:
        url = "https://app.omie.com.br/api/v1/geral/produtos/"
        
        # Vamos tentar o comando de consulta direta, que ignora filtros de listagem
        payload = {
            "call": "ConsultarProduto",
            "app_key": app_key,
            "app_secret": app_secret,
            "param": [{
                "codigo": codigo_alvo.strip() # Busca pelo código visual do produto
            }]
        }

        try:
            st.info(f"Perguntando ao Omie: 'Você conhece o produto {codigo_alvo}?'")
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                prod = response.json()
                st.balloons()
                st.success("✅ ACHEI! O produto existe e a API conseguiu ler.")
                
                # Mostra os dados principais
                st.json({
                    "Nome": prod.get("descricao"),
                    "Preço": prod.get("valor_unitario"),
                    "Estoque (Info Cadastro)": prod.get("estoque_minimo"),
                    "Origem": prod.get("origem_mercadoria")
                })
                st.success("Diagnóstico: O problema está apenas na LISTAGEM (paginação), mas a consulta direta funciona!")
                
            elif response.status_code == 500:
                erro = response.json()
                msg = erro.get("faultstring", "")
                st.error(f"❌ Erro 500: {msg}")
                
                if "TAG [CODIGO]" in msg or "nao encontrado" in msg.lower():
                    st.warning("O Omie disse que esse código não existe. Tem certeza que digitou igual ao site?")
                elif "permissao" in msg.lower() or "acesso" in msg.lower():
                    st.error("🚨 PROBLEMA ENCONTRADO: PERMISSÃO NEGADA. A chave não pode ver produtos.")
            else:
                st.error(f"Erro desconhecido: {response.status_code} - {response.text}")

        except Exception as e:
            st.error(f"Erro técnico: {e}")
