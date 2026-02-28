from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_ # Importante para a validação lógica
from database import engine, Base, get_db
from pydantic import BaseModel
from datetime import date
from typing import Optional, List
import models
import services
import traceback

# --- CRIAÇÃO DAS TABELAS ---
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- PYDANTIC MODELS ---
class EmpresaBase(BaseModel):
    nome: str

class EmpresaResponse(EmpresaBase):
    id: int
    class Config:
        from_attributes = True

class ReembolsoBase(BaseModel):
    numero_nota: str
    estabelecimento: str
    valor: float
    data_emissao: date
    centro_custo: str
    arquivo_nome: str
    comprovante_base64: Optional[str] = None
    empresa_id: Optional[int] = None

class ReembolsoUpdate(BaseModel):
    numero_nota: str
    estabelecimento: str
    valor: float
    data_emissao: date
    centro_custo: str
    empresa_id: Optional[int] = None

# --- ROTAS ---

@app.post("/empresas/", response_model=EmpresaResponse)
def criar_empresa(empresa: EmpresaBase, db: Session = Depends(get_db)):
    db_empresa = db.query(models.Empresa).filter(models.Empresa.nome == empresa.nome).first()
    if db_empresa:
        raise HTTPException(status_code=400, detail="Empresa já cadastrada")
    
    nova_empresa = models.Empresa(nome=empresa.nome)
    db.add(nova_empresa)
    db.commit()
    db.refresh(nova_empresa)
    return nova_empresa

@app.get("/empresas/", response_model=List[EmpresaResponse])
def listar_empresas(db: Session = Depends(get_db)):
    return db.query(models.Empresa).all()

@app.post("/analisar/")
async def analisar_nota(file: UploadFile = File(...)):
    print(f"🔍 Analisando: {file.filename}")
    try:
        conteudo = await file.read()
        dados_ia = services.extrair_dados_gemini(conteudo, file.content_type, file.filename)
        
        if not dados_ia:
            raise HTTPException(status_code=500, detail="IA não conseguiu ler o arquivo.")

        dados_ia['arquivo_nome'] = file.filename
        return dados_ia 

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# --- ROTA SALVAR COM VALIDAÇÃO 2 DE 3 ---
@app.post("/salvar/")
def salvar_reembolso(item: ReembolsoBase, db: Session = Depends(get_db)):
    print(f"💾 Tentando salvar: {item.estabelecimento}")

    # LÓGICA DE DUPLICIDADE (REGRA 2 DE 3)
    # Verifica se existe algum registro que tenha (Nota E Data) OU (Nota E Valor) OU (Data E Valor) iguais
    duplicado = db.query(models.Reembolso).filter(
        or_(
            and_(models.Reembolso.numero_nota == item.numero_nota, models.Reembolso.data_emissao == item.data_emissao),
            and_(models.Reembolso.numero_nota == item.numero_nota, models.Reembolso.valor == item.valor),
            and_(models.Reembolso.data_emissao == item.data_emissao, models.Reembolso.valor == item.valor)
        )
    ).first()

    if duplicado:
        # Descobre quais campos bateram para avisar o usuário
        campos_repetidos = []
        if duplicado.numero_nota == item.numero_nota: campos_repetidos.append("Número da Nota")
        if duplicado.data_emissao == item.data_emissao: campos_repetidos.append("Data de Emissão")
        if duplicado.valor == item.valor: campos_repetidos.append("Valor")
        
        msg_erro = f"Recusado! Duplicidade detectada nos campos: {', '.join(campos_repetidos)}."
        print(f"❌ {msg_erro}")
        raise HTTPException(status_code=400, detail=msg_erro)

    # Se passou, salva
    novo_reembolso = models.Reembolso(
        numero_nota=item.numero_nota,
        data_emissao=item.data_emissao,
        valor=item.valor,
        estabelecimento=item.estabelecimento,
        centro_custo=item.centro_custo,
        arquivo_nome=item.arquivo_nome,
        comprovante_base64=item.comprovante_base64,
        empresa_id=item.empresa_id,
        status="Aprovado"
    )
    
    db.add(novo_reembolso)
    db.commit()
    db.refresh(novo_reembolso)
    return {"status": "sucesso", "id": novo_reembolso.id}

@app.get("/reembolsos/")
def listar_reembolsos(db: Session = Depends(get_db)):
    return db.query(models.Reembolso).order_by(models.Reembolso.id.desc()).all()

@app.put("/reembolsos/{reembolso_id}")
def atualizar_reembolso(reembolso_id: int, item: ReembolsoUpdate, db: Session = Depends(get_db)):
    db_reembolso = db.query(models.Reembolso).filter(models.Reembolso.id == reembolso_id).first()
    if not db_reembolso:
        raise HTTPException(status_code=404, detail="Reembolso não encontrado")
    
    db_reembolso.numero_nota = item.numero_nota
    db_reembolso.estabelecimento = item.estabelecimento
    db_reembolso.valor = item.valor
    db_reembolso.data_emissao = item.data_emissao
    db_reembolso.centro_custo = item.centro_custo
    db_reembolso.empresa_id = item.empresa_id
    
    db.commit()
    db.refresh(db_reembolso)
    return {"status": "atualizado", "dados": db_reembolso}

@app.delete("/reembolsos/{reembolso_id}")
def deletar_reembolso(reembolso_id: int, db: Session = Depends(get_db)):
    db_reembolso = db.query(models.Reembolso).filter(models.Reembolso.id == reembolso_id).first()
    if not db_reembolso:
        raise HTTPException(status_code=404, detail="Reembolso não encontrado")
    
    db.delete(db_reembolso)
    db.commit()
    return {"status": "deletado"}