import google.generativeai as genai

# Sua chave
API_KEY = "AIzaSyCUpbaoxFtf4rZKpONYHfAhfgQpceOFtcU"
genai.configure(api_key=API_KEY)

print("--- 🔍 CONSULTANDO O GOOGLE ---")
print("Perguntando quais modelos estão disponíveis para sua chave...")

try:
    # Lista todos os modelos disponíveis na sua conta
    modelos = genai.list_models()
    encontrou = False
    
    for m in modelos:
        # Filtra apenas modelos que geram texto/chat
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ MODELO DISPONÍVEL: {m.name}")
            encontrou = True
            
    if not encontrou:
        print("❌ Nenhum modelo de geração de texto encontrado para essa chave.")
        print("Dica: Verifique se a 'Generative Language API' está ativada no Google Cloud Console.")

except Exception as e:
    print(f"❌ ERRO DE CONEXÃO: {e}")