from sqlalchemy import Column, Integer, String, Float, Date, Text
from database import Base

class Reembolso(Base):
    __tablename__ = "reembolsos"

    id = Column(Integer, primary_key=True, index=True)
    numero_nota = Column(String, index=True)
    data_emissao = Column(Date)
    valor = Column(Float)
    estabelecimento = Column(String)
    centro_custo = Column(String)
    arquivo_nome = Column(String)
    status = Column(String, default="Aprovado")
    
    # NOVA COLUNA: Guarda a imagem ou PDF convertida em texto (Base64)
    # Usamos "Text" porque strings de imagem são muito longas
    comprovante_base64 = Column(Text, nullable=True)