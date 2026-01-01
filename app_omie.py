import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Teste de Identidade Omie", layout="wide")
st.title("🆔 Em qual empresa estou conectado?")

# --- Carregar Chaves ---
if "omie" in st.secrets:
    app_key = st.secrets["omie"]["app_key"]
    app_secret = st.secrets["omie"]["app_secret"]
    st.success("🔒 Chaves carregadas.")
else:
    app_key = st.sidebar.text_input("App Key", type="password").strip()
    app_secret = st.sidebar.text_input("App Secret", type="password").strip()

if st.button("Descobrir Empresa e Produtos"):
    if not app_key or not app_secret:
        st.error("Preciso das chaves.")
    else:
        # Vamos testar 2 coisas diferentes para triangular onde estamos
        url_clientes = "https://app.omie.com.br/api/v1/geral/clientes/"
        url_produtos = "https://app.omie.com.br/api/v1/geral/produtos/"
        
        # --- TESTE 1: LISTAR CLIENTES (Prova de Vida) ---
        # Toda empresa ativa tem clientes. Se vier zero, é uma empresa fantasma/vazia.
        st.subheader("1. Quem são os Clientes desta conta?")
        try:
            payload_cli = {
                "call": "ListarClientes",
                "app_key": app_key, 
                "app_secret": app_secret,
                "param": [{"pagina": 1, "registros_por_pagina": 5}]
            }
            resp_cli = requests.post(url_clientes, json=payload_cli)
            
            if resp_cli.status_code == 200:
                data_cli = resp_cli.json()
                clientes = data_cli.get("clientes_cadastro", [])
                
                if clientes:
                    st.success(f"✅ Conectado! Encontrei {data_cli.get('total_de_registros')} clientes.")
                    st.write("Veja se reconhece esses nomes (isso confirma a empresa):")
                    # Mostra nomes para o usuário reconhecer a empresa
                    lista_nomes = [{"Nome do Cliente": c.get("nome_fantasia"), "Razão Social": c.get("razao_social")} for c in clientes]
                    st.table(pd.DataFrame(lista_nomes))
                else:
                    st.error("❌ Lista de Clientes VAZIA.")
                    st.warning("Se essa empresa tem clientes no site e aqui deu zero, a chave API está errada (gerada em outra filial vazia).")
            else:
                st.error(f"Erro ao ler clientes: {resp_cli.status_code}")
        except Exception as e:
            st.error(f"Erro técnico Clientes: {e}")

        st.markdown("---")

        # --- TESTE 2: LISTAR PRODUTOS (Sem filtros quebrados) ---
        st.subheader("2. Tentativa Limpa de Produtos")
        try:
            # Tenta buscar SEM NENHUM FILTRO extra, apenas paginação
            # Testamos as duas origens (API e Manual)
            found_any = False
            for origem in ["N", "S"]:
                label = "Manual (Padrão)" if origem == "N" else "Importado (API)"
                
                payload_prod = {
                    "call": "ListarProdutos",
                    "app_key": app_key,
                    "app_secret": app_secret,
                    "param": [{
                        "pagina": 1, 
                        "registros_por_pagina": 5, 
                        "apenas_importado_api": origem
                    }]
                }
                
                resp_prod = requests.post(url_produtos, json=payload_prod)
                if resp_prod.status_code == 200:
                    data_prod = resp_prod.json()
                    lista_prod = data_prod.get("produto_servico_cadastro", [])
                    if lista_prod:
                        st.success(f"✅ Sucesso na busca {label}! Exibindo primeiros itens:")
                        amostra = [{"Código": p.get("codigo"), "Descrição": p.get("descricao")} for p in lista_prod]
                        st.table(pd.DataFrame(amostra))
                        found_any = True
                    else:
                        st.info(f"Busca {label}: Retornou 0 produtos.")
                else:
                    st.write(f"Erro na busca {label}: {resp_prod.status_code}")

            if not found_any:
                st.error("⚠️ Resumo: A chave é válida, mas não achou produtos em nenhum modo.")
                st.markdown("""
                **Diagnóstico Provável:**
                1. Olhe o **Teste 1 (Clientes)** acima. 
                2. Se os clientes que apareceram NÃO SÃO da empresa que tem os produtos "Tubo", então **a chave API foi gerada na empresa errada**.
                3. Entre no Omie, troque a empresa no topo, vá em Configurações > API e gere uma chave nova lá.
                """)

        except Exception as e:
            st.error(f"Erro técnico Produtos: {e}")
