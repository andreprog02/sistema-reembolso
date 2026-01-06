import google.generativeai as genai

# COLE SUA API KEY AQUI DENTRO DAS ASPAS
API_KEY = "AIzaSyCUpbaoxFtf4rZKpONYHfAhfgQpceOFtcU" 

genai.configure(api_key=API_KEY)

print("Listando modelos disponíveis para sua chave...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"Erro ao listar: {e}")