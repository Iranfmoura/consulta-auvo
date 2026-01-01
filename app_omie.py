import streamlit as st
import requests
import pandas as pd
import json

st.set_page_config(page_title="Consulta Omie", layout="wide")
st.title("🏭 Consulta Produtos - Omie")

# --- Carregar Chaves ---
if "omie" in st.secrets:
    app_key = st.secrets["omie"]["app_key"]
    app_secret = st.secrets["omie"]["app_secret"]
    st.success("🔒 Chaves Omie Carregadas")
else:
    st.sidebar.header("Credenciais Omie")
    app_key = st.sidebar.text_input("App Key", type="password").strip()
    app_secret = st.sidebar.text_input("App Secret", type="password").strip()
    st.warning("⚠️ Modo Manual")

# --- Configuração ---
MAX_PAGINAS = 10  # Lê até 10 páginas (500 produtos)
ITENS_POR_PAGINA = 50

termo = st.text_input("Nome do Produto no Omie", placeholder="Ex: Tubo")

if st.button("Buscar no Omie"):
    if not app_key or not app_secret:
        st.error("Preencha as chaves.")
    else:
        url = "https://app.omie.com.br/api/v1/geral/produtos/"
        produtos_encontrados = []
        paginas_lidas = 0
        total_lido = 0
        
        barra = st.progress(0, text="Iniciando...")
        
        try:
            for pagina in range(1, MAX_PAGINAS + 1):
                paginas_lidas = pagina
                
                # --- CORREÇÃO: REMOVI FILTROS EXTRAS ---
                # Enviamos apenas o básico para pegar TUDO
                payload = {
                    "call": "ListarProdutos",
                    "app_key": app_key,
                    "app_secret": app_secret,
                    "param": [{
                        "pagina": pagina,
                        "registros_por_pagina": ITENS_POR_PAGINA
                    }]
                }
                
                barra.progress(int((pagina / MAX_PAGINAS) * 100), text=f"Lendo página {pagina}...")
                
                response = requests.post(url, json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    lista_lote = data.get("produto_servico_cadastro", [])
                    
                    if not lista_lote:
                        # Se acabou os produtos, para o loop
                        break
                    
                    total_lido += len(lista_lote)

                    # Filtra no Python
                    termo_lower = termo.lower()
                    for item in lista_lote:
                        descricao = item.get("descricao", "").lower()
                        codigo = str(item.get("codigo", "")).lower()
                        
                        if termo_lower in descricao or termo_lower in codigo:
                            produtos_encontrados.append({
                                "Código": item.get("codigo"),
                                "Descrição": item.get("descricao"),
                                "Preço": f"R$ {item.get('valor_unitario', 0)}",
                                "NCM": item.get("ncm"),
                                "ID Omie": item.get("codigo_produto")
                            })
                    
                    # Se já achou 20 produtos, pode parar para não demorar muito
                    if len(produtos_encontrados) >= 20:
                        break
                else:
                    st.error(f"Erro na pág {pagina}: {response.status_code}")
                    break
            
            barra.empty()

            if produtos_encontrados:
                df = pd.DataFrame(produtos_encontrados)
                st.success(f"{len(df)} produtos encontrados (Varri {total_lido} itens).")
                st.dataframe(df, use_container_width=True)
            else:
                st.warning(f"O Omie retornou {total_lido} produtos no total, mas nenhum continha o nome '{termo}'.")
                
                # Dica se continuar zerado
                if total_lido == 0:
                    st.info("💡 Dica: Verifique se você gerou as chaves API na empresa correta dentro do Omie (caso tenha mais de uma).")

        except Exception as e:
            st.error(f"Erro técnico: {e}")
