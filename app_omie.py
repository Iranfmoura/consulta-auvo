import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Consulta Omie Pro", layout="wide")
st.title("🏭 Consulta Estoque & Preço - Omie")

# --- Carregar Chaves ---
if "omie" in st.secrets:
    app_key = st.secrets["omie"]["app_key"]
    app_secret = st.secrets["omie"]["app_secret"]
    st.sidebar.success("🔒 Chaves Seguras Ativas")
else:
    st.sidebar.header("Configuração")
    app_key = st.sidebar.text_input("App Key", type="password").strip()
    app_secret = st.sidebar.text_input("App Secret", type="password").strip()

# --- Interface Principal ---
aba1, aba2 = st.tabs(["🔍 Buscar por Nome", "🎯 Buscar por Código (Preciso)"])

# --- ABA 1: BUSCA POR NOME (Depende de Permissão de Listagem) ---
with aba1:
    st.markdown("Use esta aba para pesquisar partes do nome (Ex: 'tubo').")
    termo = st.text_input("Nome do Produto:", placeholder="Digite para buscar...", key="busca_nome")
    
    if st.button("Pesquisar Nome"):
        if not app_key:
            st.error("Chaves não configuradas.")
        else:
            url = "https://app.omie.com.br/api/v1/geral/produtos/"
            produtos = []
            erro_permissao = False
            
            # Barra de progresso visual
            barra = st.progress(0, text="Iniciando varredura...")
            
            try:
                # Busca até 10 páginas (500 itens)
                for pagina in range(1, 11):
                    # TRUQUE: Não mandamos filtro de importado para vir TUDO
                    payload = {
                        "call": "ListarProdutos",
                        "app_key": app_key,
                        "app_secret": app_secret,
                        "param": [{"pagina": pagina, "registros_por_pagina": 50, "exibir_obs": "N"}]
                    }
                    
                    barra.progress(pagina * 10, text=f"Lendo página {pagina}...")
                    response = requests.post(url, json=payload)
                    
                    if response.status_code == 200:
                        data = response.json()
                        lote = data.get("produto_servico_cadastro", [])
                        if not lote: break # Fim da lista
                        
                        termo_lower = termo.lower().strip()
                        for item in lote:
                            desc = item.get("descricao", "").lower()
                            cod = str(item.get("codigo", "")).lower()
                            
                            if termo_lower in desc or termo_lower in cod:
                                produtos.append({
                                    "Código": item.get("codigo"),
                                    "Descrição": item.get("descricao"),
                                    "Preço": f"R$ {item.get('valor_unitario')}",
                                    "NCM": item.get("ncm"),
                                    "ID": item.get("codigo_produto")
                                })
                    elif response.status_code == 500:
                        erro_msg = response.json().get("faultstring", "")
                        if "permissao" in erro_msg.lower() or "denied" in erro_msg.lower():
                            erro_permissao = True
                        break # Para o loop em caso de erro
                
                barra.empty()
                
                if produtos:
                    df = pd.DataFrame(produtos)
                    st.success(f"✅ Encontrados {len(df)} produtos.")
                    st.dataframe(df, use_container_width=True)
                else:
                    st.warning("Nenhum produto encontrado com esse nome.")
                    if erro_permissao:
                        st.error("🚨 ALERTA: Sua chave API parece não ter permissão para LISTAR produtos. Tente usar a busca por Código.")
                    else:
                        st.info("Dica: Se a lista veio vazia mas o produto existe, verifique as Permissões do Usuário da API no Omie.")

            except Exception as e:
                st.error(f"Erro técnico: {e}")

# --- ABA 2: BUSCA POR CÓDIGO (Funciona Sempre) ---
with aba2:
    st.markdown("Use esta aba se souber o código exato (Ex: '946'). **Funciona mesmo com permissão restrita.**")
    cod_exato = st.text_input("Código do Produto:", key="busca_cod")
    
    if st.button("Consultar Código"):
        if not app_key or not cod_exato:
            st.warning("Preencha o código.")
        else:
            url = "https://app.omie.com.br/api/v1/geral/produtos/"
            payload = {
                "call": "ConsultarProduto",
                "app_key": app_key,
                "app_secret": app_secret,
                "param": [{"codigo": cod_exato.strip()}]
            }
            
            try:
                resp = requests.post(url, json=payload)
                if resp.status_code == 200:
                    p = resp.json()
                    st.balloons()
                    
                    # Layout Bonito para o Produto
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Preço", f"R$ {p.get('valor_unitario')}")
                    col2.metric("Código", p.get("codigo"))
                    col3.metric("NCM", p.get("ncm"))
                    
                    st.subheader(p.get("descricao"))
                    
                    # Detalhes extras
                    st.json({
                        "Família": p.get("descricao_familia", "-"),
                        "Origem": p.get("origem_mercadoria"),
                        "Peso Líquido": p.get("peso_liq"),
                        "Status": "Inativo" if p.get("inativo") == "S" else "Ativo"
                    })
                else:
                    st.error("Produto não encontrado ou erro na consulta.")
                    st.write(resp.text)
            except Exception as e:
                st.error(f"Erro: {e}")
