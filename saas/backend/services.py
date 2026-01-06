import google.generativeai as genai
import json
import re
import time
from datetime import datetime, date

# --- CONFIGURAÇÃO ---
API_KEY = "AIzaSyCUpbaoxFtf4rZKpONYHfAhfgQpceOFtcU"
genai.configure(api_key=API_KEY)

def extrair_dados_gemini(conteudo_arquivo, tipo_mime, nome_arquivo):
    print(f"--- 🚀 INICIANDO LEITURA IA: {nome_arquivo} ---")
    
    # Vamos focar no 2.5 Flash que funcionou antes. 
    # Se ele falhar, tentamos o 2.0.
    modelos_para_tentar = [
        'gemini-2.5-flash',     
        'gemini-2.0-flash',     
        'gemini-flash-latest'
    ]
    
    # LOOP PRINCIPAL: Tenta cada modelo da lista
    for modelo_atual in modelos_para_tentar:
        
        # LOOP DE INSISTÊNCIA: Tenta o MESMO modelo até 3 vezes
        tentativas_maximas = 3
        for i in range(tentativas_maximas):
            try:
                print(f"📡 ({i+1}/{tentativas_maximas}) Conectando com {modelo_atual}...")
                
                model = genai.GenerativeModel(modelo_atual)
                
                prompt = """
                Analise este documento financeiro. Extraia:
                1. Número da nota (apenas numeros).
                2. Data de emissão (Formato YYYY-MM-DD).
                3. Valor total.
                4. Nome do estabelecimento.
                
                Retorne APENAS JSON puro:
                {"numero_nota": "string", "data_emissao": "YYYY-MM-DD", "valor": 0.00, "estabelecimento": "string"}
                """
                
                part_dados = {"mime_type": tipo_mime, "data": conteudo_arquivo}
                
                # Chamada para o Google
                response = model.generate_content([prompt, part_dados])
                print(f"✅ SUCESSO! O modelo {modelo_atual} respondeu.")
                
                # --- SUCESSO! PROCESSA E RETORNA ---
                texto_limpo = re.sub(r"```json|```|json", "", response.text).strip()
                dados = json.loads(texto_limpo)
                
                try:
                    dados['data_emissao'] = datetime.strptime(dados['data_emissao'], '%Y-%m-%d').date()
                except:
                    dados['data_emissao'] = date.today()
                    
                return dados 
                # -----------------------------------

            except Exception as e:
                erro_str = str(e)
                
                # CASO 1: COTA ESTOURADA (Erro 429)
                if "429" in erro_str or "quota" in erro_str.lower():
                    # Aumentei para 25 segundos. É o tempo que o Google precisa para "esfriar".
                    tempo_espera = 25 
                    print(f"⏳ Cota cheia no Google. Aguardando {tempo_espera}s para liberar a API...")
                    time.sleep(tempo_espera)
                    # O 'continue' faz ele tentar o MESMO modelo de novo após esperar
                    continue 
                
                # CASO 2: MODELO NÃO EXISTE (Erro 404)
                elif "404" in erro_str or "not found" in erro_str.lower():
                    print(f"🔸 Modelo {modelo_atual} não disponível para sua chave. Pulando para o próximo...")
                    break # Sai do loop interno e vai para o próximo modelo da lista
                
                else:
                    print(f"❌ Erro inesperado: {e}")
                    break # Sai do loop interno

    print("❌❌❌ FALHA TOTAL: Não foi possível ler a nota após várias tentativas.")
    return None