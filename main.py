import streamlit as st
import pandas as pd
from datetime import date, datetime
import google.generativeai as genai
from PIL import Image
import json
import re

# --- 1. CONFIGURAÇÃO E ESTILO ---
st.set_page_config(
    page_title="Reembolso Corp",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ⚠️ SUA CHAVE API
API_KEY = "AIzaSyCUpbaoxFtf4rZKpONYHfAhfgQpceOFtcU"
genai.configure(api_key=API_KEY)

# Inicializa Banco de Dados
if 'banco_dados' not in st.session_state:
    st.session_state['banco_dados'] = []

# --- 2. FUNÇÕES DE BACKEND (Lógica) ---
def extrair_dados_reais_gemini(arquivo_upload):
    try:
        tipo_arquivo = arquivo_upload.type
        part_dados = None
        
        if "pdf" in tipo_arquivo:
            part_dados = {"mime_type": "application/pdf", "data": arquivo_upload.getvalue()}
        else:
            part_dados = {"mime_type": tipo_arquivo, "data": arquivo_upload.getvalue()}
        
        model = genai.GenerativeModel('models/gemini-2.5-flash')
        
        prompt = """
        Analise este documento financeiro. Extraia:
        1. Número da nota/cupom (apenas alfanumérico).
        2. Data de emissão (Formato YYYY-MM-DD).
        3. Valor total.
        4. Nome do estabelecimento.
        
        Retorne APENAS JSON puro:
        {"numero_nota": "string", "data_emissao": "YYYY-MM-DD", "valor": 0.00, "estabelecimento": "string"}
        """
        
        response = model.generate_content([prompt, part_dados])
        texto_limpo = re.sub(r"```json|```|json", "", response.text).strip()
        dados_json = json.loads(texto_limpo)
        dados_json['arquivo_nome'] = arquivo_upload.name
        
        try:
            dados_json['data_emissao'] = datetime.strptime(dados_json['data_emissao'], '%Y-%m-%d').date()
        except:
            dados_json['data_emissao'] = date.today()
            
        return dados_json
    except Exception as e:
        st.error(f"Erro na leitura: {e}")
        return None

def verificar_duplicidade(nova_nota, nova_data, novo_valor):
    for item in st.session_state['banco_dados']:
        mesma_nota = str(item['nota']).strip().lower() == str(nova_nota).strip().lower()
        mesma_data = item['data'] == nova_data
        mesmo_valor = abs(float(item['valor']) - float(novo_valor)) < 0.01
        if mesma_nota and mesma_data and mesmo_valor:
            return True
    return False

# --- 3. LAYOUT E INTERFACE ---

# --- SIDEBAR (Resumo Geral) ---
with st.sidebar:
    st.title("💼 Painel")
    st.markdown("---")
    
    # Métricas Rápidas
    if len(st.session_state['banco_dados']) > 0:
        df_side = pd.DataFrame(st.session_state['banco_dados'])
        total_geral = df_side['valor'].sum()
        qtd_notas = len(df_side)
        
        st.metric("Total Acumulado", f"R$ {total_geral:,.2f}")
        st.metric("Notas Cadastradas", f"{qtd_notas}")
        
        st.markdown("---")
        # Gráfico simples de pizza por centro de custo
        st.caption("Distribuição por Categoria")
        st.bar_chart(df_side['centro_custo'].value_counts(), color="#4CAF50")
    else:
        st.info("Sem dados para resumo.")

# --- ÁREA PRINCIPAL ---
st.title("Sistema de Gestão de Reembolsos")

aba_novo, aba_gestao = st.tabs(["➕ Novo Lançamento", "📁 Gerenciar Histórico"])

# === ABA 1: NOVO LANÇAMENTO ===
with aba_novo:
    # Cria um container para separar visualmente
    with st.container(border=True):
        col_upload, col_preview = st.columns([2, 1])
        
        with col_upload:
            st.subheader("1. Upload do Documento")
            arquivo = st.file_uploader("Arraste ou selecione (PDF/JPG)", type=['png', 'jpg', 'jpeg', 'pdf'])
            
            if arquivo and st.button("🚀 Processar Documento com IA", use_container_width=True, type="primary"):
                 with st.spinner("Analisando pixels e textos..."):
                    dados_lidos = extrair_dados_reais_gemini(arquivo)
                    if dados_lidos:
                        st.session_state['dados_temp'] = dados_lidos
        
        with col_preview:
            if arquivo:
                st.caption("Pré-visualização:")
                if "pdf" in arquivo.type:
                    st.image("https://upload.wikimedia.org/wikipedia/commons/8/87/PDF_file_icon.svg", width=100)
                    st.text(arquivo.name)
                else:
                    st.image(arquivo, use_container_width=True)

    # Se a IA já leu, mostra o formulário de cadastro em destaque
    if 'dados_temp' in st.session_state:
        st.markdown("### 2. Conferência dos Dados")
        
        # Container com borda para destacar a área de edição
        with st.container(border=True):
            with st.form("form_final"):
                dados = st.session_state['dados_temp']
                
                # Layout em Grade (Grid)
                l1_c1, l1_c2, l1_c3 = st.columns(3)
                with l1_c1:
                    novo_num = st.text_input("Nº Nota/Cupom", value=dados.get('numero_nota', ''))
                with l1_c2:
                    val_data = dados.get('data_emissao', date.today())
                    nova_data = st.date_input("Data Emissão", value=val_data, format="DD/MM/YYYY")
                with l1_c3:
                    val_float = float(dados.get('valor', 0.0))
                    novo_valor = st.number_input("Valor Total (R$)", value=val_float, format="%.2f")

                l2_c1, l2_c2 = st.columns([2, 1])
                with l2_c1:
                    empresa = st.text_input("Estabelecimento / Fornecedor", value=dados.get('estabelecimento', ''))
                with l2_c2:
                    centro_custo = st.selectbox("Centro de Custo", 
                        ["Alimentação", "Transporte", "Combustível", "Hospedagem", "Material", "Outros"])
                
                submit = st.form_submit_button("💾 Salvar no Sistema", type="primary", use_container_width=True)
                
                if submit:
                    if verificar_duplicidade(novo_num, nova_data, novo_valor):
                        st.error("🚫 ERRO: Esta nota já consta no banco de dados!")
                    else:
                        novo_registro = {
                            "id": len(st.session_state['banco_dados']) + 1,
                            "data": nova_data,
                            "estabelecimento": empresa,
                            "centro_custo": centro_custo,
                            "valor": novo_valor,
                            "nota": novo_num,
                            "arquivo": dados['arquivo_nome'],
                            "status": "Pendente" # Campo novo para futuro
                        }
                        st.session_state['banco_dados'].append(novo_registro)
                        st.balloons()
                        st.toast("✅ Lançamento realizado com sucesso!")
                        del st.session_state['dados_temp']
                        st.rerun()

# === ABA 2: GESTÃO ===
with aba_gestao:
    if len(st.session_state['banco_dados']) > 0:
        
        # Filtros no topo dentro de um expander para não poluir
        with st.expander("🔍 Filtros de Busca", expanded=True):
            f1, f2, f3 = st.columns(3)
            df = pd.DataFrame(st.session_state['banco_dados'])
            
            data_ini = f1.date_input("De:", value=date(2025, 1, 1), format="DD/MM/YYYY")
            data_fim = f2.date_input("Até:", value=date.today(), format="DD/MM/YYYY")
            filtro_custo = f3.multiselect("Filtrar Centro de Custo", df['centro_custo'].unique())
            
            # Lógica de Filtro
            mask = (df['data'] >= data_ini) & (df['data'] <= data_fim)
            if filtro_custo:
                mask = mask & (df['centro_custo'].isin(filtro_custo))
            
            df_filtrado = df.loc[mask]

        st.subheader("Tabela de Lançamentos")
        st.caption("Edite os valores diretamente na tabela abaixo.")

        # Tabela Editável Moderna
        df_editado = st.data_editor(
            df_filtrado,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
                "data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                "status": st.column_config.SelectboxColumn("Status", options=["Pendente", "Aprovado", "Pago"]),
                "arquivo": st.column_config.TextColumn("Arquivo", disabled=True)
            },
            hide_index=True,
            key="editor_dados"
        )
        
        col_save, col_info = st.columns([1, 3])
        with col_save:
            if st.button("💾 Salvar Alterações", type="primary"):
                st.session_state['banco_dados'] = df_editado.to_dict('records')
                st.success("Dados atualizados!")
                st.rerun()
        
        # Cards de Resumo do Filtro Atual
        st.divider()
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Filtrado", f"R$ {df_editado['valor'].sum():,.2f}")
        m2.metric("Itens Listados", len(df_editado))
        if len(df_editado) > 0:
            ticket_medio = df_editado['valor'].mean()
            m3.metric("Ticket Médio", f"R$ {ticket_medio:,.2f}")
            
    else:
        st.warning("📭 O histórico está vazio. Faça o primeiro lançamento na aba anterior.")