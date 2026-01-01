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
            # --- ESTRATÉGIA DUPLA: Tenta 'N' (Manual) e depois 'S' (API) ---
            # Assim garantimos que pegamos produtos cadastrados na mão E importados
            tipos_importacao = ["N", "S"] 
            
            for tipo in tipos_importacao:
                origem_txt = "Manuais" if tipo == "N" else "Importados via API"
                
                for pagina in range(1, MAX_PAGINAS + 1):
                    
                    payload = {
                        "call": "ListarProdutos",
                        "app_key": app_key,
                        "app_secret": app_secret,
                        "param": [{
                            "pagina": pagina,
                            "registros_por_pagina": ITENS_POR_PAGINA,
                            "apenas_importado_api": tipo  # Aqui está o pulo do gato!
                        }]
                    }
                    
                    barra.progress(int((pagina / MAX_PAGINAS) * 50) + (50 if tipo == 'S' else 0), 
                                 text=f"Lendo {origem_txt} - Pág {pagina}...")
                    
                    response = requests.post(url, json=payload)
                    
                    if response.status_code == 200:
                        data = response.json()
                        lista_lote = data.get("produto_servico_cadastro", [])
                        
                        if not lista_lote:
                            break # Acabou essa lista, vai para o próximo tipo
                        
                        total_lido += len(lista_lote)

                        # Filtra no Python
                        termo_lower = termo.lower().strip()
                        for item in lista_lote:
                            descricao = item.get("descricao", "").lower()
                            codigo = str(item.get("codigo", "")).lower()
                            
                            # Se o usuário não digitou nada, traz tudo. Se digitou, filtra.
                            if not termo_lower or (termo_lower in descricao or termo_lower in codigo):
                                produtos_encontrados.append({
                                    "Código": item.get("codigo"),
                                    "Descrição": item.get("descricao"),
                                    "Preço": f"R$ {item.get('valor_unitario', 0)}",
                                    "NCM": item.get("ncm"),
                                    "Origem": origem_txt, # Pra vc saber de onde veio
                                    "ID Omie": item.get("codigo_produto")
                                })
                        
                        # Trava de segurança para não explodir a memória se buscar vazio
                        if len(produtos_encontrados) >= 100:
                            break
                    else:
                        st.error(f"Erro na pág {pagina}: {response.status_code}")
                        break
                
                # Se já achou o suficiente no primeiro tipo, nem busca no segundo
                if len(produtos_encontrados) >= 100:
                    break

            barra.empty()

            if produtos_encontrados:
                df = pd.DataFrame(produtos_encontrados)
                # Remove duplicatas caso o mesmo produto apareça (raro, mas possível)
                df = df.drop_duplicates(subset=['ID Omie'])
                
                st.success(f"{len(df)} produtos encontrados (Varri {total_lido} itens).")
                st.dataframe(df, use_container_width=True)
            else:
                st.warning(f"O Omie retornou {total_lido} registros no total, mas nenhum continha o nome '{termo}'.")
                if total_lido > 0:
                     st.info("Pelo menos agora a conexão trouxe dados! Tente buscar por uma parte menor do nome.")
                else:
                     st.error("Ainda retornou 0. Verifique se os produtos não estão Inativos no Omie.")

        except Exception as e:
            st.error(f"Erro técnico: {e}")
