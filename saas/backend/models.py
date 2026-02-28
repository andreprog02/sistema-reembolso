from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Empresa(Base):
    __tablename__ = "empresas"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, unique=True, index=True)

    # Relacionamento inverso: Uma empresa tem vários reembolsos
    reembolsos = relationship("Reembolso", back_populates="empresa")

class Reembolso(Base):
    __tablename__ = "reembolsos"

    id = Column(Integer, primary_key=True, index=True)
    numero_nota = Column(String, index=True)
    data_emissao = Column(Date)
    valor = Column(Float)
    estabelecimento = Column(String)
    centro_custo = Column(String)
    status = Column(String, default="Pendente")
    
    # Campos para o arquivo/comprovante
    arquivo_nome = Column(String, nullable=True)
    comprovante_base64 = Column(String, nullable=True)

    # Vínculo com a Tabela Empresa
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=True)
    empresa = relationship("Empresa", back_populates="reembolsos")