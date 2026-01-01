import streamlit as st
import requests
import pandas as pd
import json

# --- Configuração da Página ---
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

# --- Configuração da Busca ---
MAX_PAGINAS = 10  # Quantas páginas ele vai ler (10 páginas x 50 itens = 500 itens)
ITENS_POR_PAGINA = 50 # Reduzimos para 50 para não travar o servidor (Erro SOAP)

# --- Área de Busca ---
termo = st.text_input("Nome do Produto no Omie", placeholder="Ex: Tubo")

if st.button("Buscar no Omie"):
    if not app_key or not app_secret:
        st.error("Preencha a App Key e o App Secret.")
    else:
        url = "https://app.omie.com.br/api/v1/geral/produtos/"
        produtos_encontrados = []
        paginas_lidas = 0
        total_lido = 0
        
        # Barra de progresso para o usuário ver que está rodando
        barra_progresso = st.progress(0, text="Iniciando busca...")
        
        try:
            # --- LOOP: Busca página por página ---
            for pagina in range(1, MAX_PAGINAS + 1):
                paginas_lidas = pagina
                
                payload = {
                    "call": "ListarProdutos",
                    "app_key": app_key,
                    "app_secret": app_secret,
                    "param": [{
                        "pagina": pagina,
                        "registros_por_pagina": ITENS_POR_PAGINA,
                        "apenas_importado_api": "N"
                    }]
                }
                
                # Atualiza a barra
                barra_progresso.progress(int((pagina / MAX_PAGINAS) * 100), text=f"Lendo página {pagina} de {MAX_PAGINAS}...")
                
                response = requests.post(url, json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    lista_lote = data.get("produto_servico_cadastro", [])
                    total_registros = data.get("total_de_registros", 0) # Quantos existem no total
                    
                    if not lista_lote:
                        break # Se veio vazio, acabou o estoque, para de buscar
                    
                    total_lido += len(lista_lote)

                    # Filtra este lote no Python
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
                                "Unidade": item.get("unidade"),
                                "ID Omie": item.get("codigo_produto")
                            })
                    
                    # Opcional: Se já achou muitos (ex: 20), pode parar para não demorar
                    if len(produtos_encontrados) >= 20:
                        break
                        
                elif response.status_code == 500:
                    # Se der erro 500, mostramos e paramos
                    erro_msg = response.json().get("faultstring", "Erro desconhecido")
                    # Ignora erro "No Records Found" no final da lista
                    if "NO-RECORDS-FOUND" not in str(response.text):
                        st.error(f"Erro na página {pagina}: {erro_msg}")
                    break
                else:
                    st.error(f"Erro de conexão: {response.status_code}")
                    break
            
            barra_progresso.empty() # Limpa a barra quando termina

            # --- RESULTADO FINAL ---
            if produtos_encontrados:
                df = pd.DataFrame(produtos_encontrados)
                st.success(f"{len(df)} produtos encontrados (Varri {total_lido} itens em {paginas_lidas} páginas).")
                st.dataframe(df, use_container_width=True)
            else:
                st.warning(f"Li {total_lido} produtos e não encontrei '{termo}'. Tente aumentar o MAX_PAGINAS no código.")

        except Exception as e:
            st.error(f"Erro técnico: {e}")

st.markdown("---")
st.caption(f"Configuração: {ITENS_POR_PAGINA} itens/pág | Máx {MAX_PAGINAS} páginas")
