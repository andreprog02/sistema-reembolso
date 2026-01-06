from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import engine, Base, get_db
from pydantic import BaseModel
from datetime import date
from typing import Optional
import models
import services
import traceback

# Recria as tabelas (Lembre de apagar o reembolsos.db antigo antes!)
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELO DE DADOS ---
class ReembolsoBase(BaseModel):
    numero_nota: str
    estabelecimento: str
    valor: float
    data_emissao: date
    centro_custo: str
    arquivo_nome: str
    comprovante_base64: Optional[str] = None # Campo novo

class ReembolsoUpdate(BaseModel):
    numero_nota: str
    estabelecimento: str
    valor: float
    data_emissao: date
    centro_custo: str

# --- ROTA 1: ANALISAR (IA) ---
@app.post("/analisar/")
async def analisar_nota(file: UploadFile = File(...)):
    print(f"🔍 Analisando: {file.filename}")
    try:
        conteudo = await file.read()
        dados_ia = services.extrair_dados_gemini(conteudo, file.content_type, file.filename)
        
        if not dados_ia:
            raise HTTPException(status_code=500, detail="IA não conseguiu ler.")

        dados_ia['arquivo_nome'] = file.filename
        return dados_ia 

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# --- ROTA 2: CRIAR (Salvar Novo) ---
@app.post("/salvar/")
def salvar_reembolso(item: ReembolsoBase, db: Session = Depends(get_db)):
    print(f"💾 Salvando novo item: {item.estabelecimento}")
    
    # Cria o registro
    novo_reembolso = models.Reembolso(
        numero_nota=item.numero_nota,
        data_emissao=item.data_emissao,
        valor=item.valor,
        estabelecimento=item.estabelecimento,
        centro_custo=item.centro_custo,
        arquivo_nome=item.arquivo_nome,
        comprovante_base64=item.comprovante_base64, # Salva a imagem
        status="Aprovado"
    )
    
    db.add(novo_reembolso)
    db.commit()
    db.refresh(novo_reembolso)
    return {"status": "sucesso", "id": novo_reembolso.id}

# --- ROTA 3: LISTAR ---
@app.get("/reembolsos/")
def listar_reembolsos(db: Session = Depends(get_db)):
    return db.query(models.Reembolso).order_by(models.Reembolso.id.desc()).all()

# --- ROTA 4: ATUALIZAR (Editar existente) ---
@app.put("/reembolsos/{reembolso_id}")
def atualizar_reembolso(reembolso_id: int, item: ReembolsoUpdate, db: Session = Depends(get_db)):
    db_reembolso = db.query(models.Reembolso).filter(models.Reembolso.id == reembolso_id).first()
    if not db_reembolso:
        raise HTTPException(status_code=404, detail="Reembolso não encontrado")
    
    # Atualiza os campos
    db_reembolso.numero_nota = item.numero_nota
    db_reembolso.estabelecimento = item.estabelecimento
    db_reembolso.valor = item.valor
    db_reembolso.data_emissao = item.data_emissao
    db_reembolso.centro_custo = item.centro_custo
    
    db.commit()
    db.refresh(db_reembolso)
    return {"status": "atualizado", "dados": db_reembolso}

# --- ROTA 5: DELETAR ---
@app.delete("/reembolsos/{reembolso_id}")
def deletar_reembolso(reembolso_id: int, db: Session = Depends(get_db)):
    db_reembolso = db.query(models.Reembolso).filter(models.Reembolso.id == reembolso_id).first()
    if not db_reembolso:
        raise HTTPException(status_code=404, detail="Reembolso não encontrado")
    
    db.delete(db_reembolso)
    db.commit()
    return {"status": "deletado"}