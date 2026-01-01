import streamlit as st
import requests
import pandas as pd
import json

# --- Configuração da Página ---
st.set_page_config(page_title="Diagnóstico Omie", layout="wide")
st.title("🕵️ Diagnóstico - O que o Omie está respondendo?")

# --- Carregar Chaves ---
if "omie" in st.secrets:
    app_key = st.secrets["omie"]["app_key"]
    app_secret = st.secrets["omie"]["app_secret"]
    st.success("🔒 Chaves Omie Carregadas")
else:
    st.sidebar.header("Credenciais Omie")
    app_key = st.sidebar.text_input("App Key", type="password").strip()
    app_secret = st.sidebar.text_input("App Secret", type="password").strip()

if st.button("Testar Conexão e Ver Resposta"):
    if not app_key or not app_secret:
        st.error("Preciso das chaves para testar.")
    else:
        url = "https://app.omie.com.br/api/v1/geral/produtos/"
        
        # Payload simples para pegar APENAS a página 1
        payload = {
            "call": "ListarProdutos",
            "app_key": app_key,
            "app_secret": app_secret,
            "param": [{
                "pagina": 1,
                "registros_por_pagina": 10, # Só 10 pra ser leve
                "apenas_importado_api": "N"
            }]
        }

        try:
            with st.spinner("Chamando servidor Omie..."):
                response = requests.post(url, json=payload)
            
            st.subheader("Resultado do Teste:")
            
            # 1. Mostra o Status Code (tem que ser 200)
            if response.status_code == 200:
                st.success(f"Status 200 (OK) - Conexão aceita!")
            else:
                st.error(f"Status {response.status_code} - Erro de conexão!")

            # 2. Mostra a RESPOSTA COMPLETA (Isso é o que precisamos ver)
            st.markdown("**Resposta Bruta do Servidor (JSON):**")
            dados = response.json()
            st.json(dados)

            # 3. Análise Rápida
            if "faultstring" in str(dados):
                st.error("ERRO ENCONTRADO NA RESPOSTA: Verifique a mensagem acima.")
            elif "produto_servico_cadastro" in dados:
                qtd = len(dados['produto_servico_cadastro'])
                st.info(f"Sucesso! Encontrei o campo correto com {qtd} produtos.")
            else:
                st.warning("Atenção: A conexão funcionou, mas não veio a lista de produtos.")

        except Exception as e:
            st.error(f"Erro técnico grave: {e}")
