import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Consulta Omie", layout="wide")
st.title("🏭 Consulta Produtos - Omie")

# --- Carregar Chaves ---
if "omie" in st.secrets:
    app_key = st.secrets["omie"]["app_key"]
    app_secret = st.secrets["omie"]["app_secret"]
    st.success("🔒 Chaves Omie Carregadas")
else:
    app_key = st.sidebar.text_input("App Key", type="password").strip()
    app_secret = st.sidebar.text_input("App Secret", type="password").strip()

# --- Configuração ---
MAX_PAGINAS = 10  # Quantas páginas ler (10 páginas x 50 produtos = 500)
ITENS_POR_PAGINA = 50 

termo = st.text_input("Nome do Produto (ou parte do nome):", placeholder="Ex: Tubo")

if st.button("Buscar no Omie"):
    if not app_key:
        st.warning("Faltam as chaves de acesso.")
    else:
        url = "https://app.omie.com.br/api/v1/geral/produtos/"
        produtos_encontrados = []
        total_lido = 0
        
        barra = st.progress(0, text="Iniciando varredura...")
        
        try:
            for pagina in range(1, MAX_PAGINAS + 1):
                # --- O SEGREDO ESTÁ AQUI ---
                # Removemos "apenas_importado_api". Agora aceita qualquer coisa (inclusive NULL).
                payload = {
                    "call": "ListarProdutos",
                    "app_key": app_key,
                    "app_secret": app_secret,
                    "param": [{
                        "pagina": pagina,
                        "registros_por_pagina": ITENS_POR_PAGINA,
                        "exibir_obs": "N" # Otimização para vir mais leve
                    }]
                }
                
                barra.progress(int((pagina / MAX_PAGINAS) * 100), text=f"Lendo página {pagina}...")
                
                response = requests.post(url, json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    lista_lote = data.get("produto_servico_cadastro", [])
                    
                    if not lista_lote:
                        break # Fim do estoque
                    
                    total_lido += len(lista_lote)

                    # Filtra no Python
                    termo_lower = termo.lower().strip()
                    for item in lista_lote:
                        descricao = item.get("descricao", "").lower()
                        codigo = str(item.get("codigo", "")).lower()
                        
                        # Se achou o termo no nome OU no código
                        if not termo_lower or (termo_lower in descricao or termo_lower in codigo):
                            
                            # Tenta pegar preço de várias formas (Omie varia as vezes)
                            preco = item.get("valor_unitario", 0)
                            
                            produtos_encontrados.append({
                                "Código": item.get("codigo"),
                                "Descrição": item.get("descricao"),
                                "Preço": f"R$ {preco}",
                                "Unidade": item.get("unidade"),
                                "NCM": item.get("ncm"),
                                "ID Omie": item.get("codigo_produto")
                            })
                    
                    # Se já encheu a tela com 50 resultados, para (pra não ficar lento)
                    if len(produtos_encontrados) >= 50:
                        break
                else:
                    st.error(f"Erro na página {pagina}: {response.status_code}")
                    break
            
            barra.empty()

            # --- RESULTADO FINAL ---
            if produtos_encontrados:
                df = pd.DataFrame(produtos_encontrados)
                st.balloons()
                st.success(f"✅ Encontrei {len(df)} produtos com o nome '{termo}'.")
                st.dataframe(df, use_container_width=True)
            else:
                if total_lido > 0:
                    st.warning(f"Li {total_lido} produtos no total, mas nenhum tinha o nome '{termo}'.")
                else:
                    st.error("A lista veio vazia. Verifique se existem produtos Ativos nesta empresa.")

        except Exception as e:
            st.error(f"Erro técnico: {e}")
