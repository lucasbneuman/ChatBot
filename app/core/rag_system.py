# app/core/rag_system.py - Sistema RAG para documentos de la empresa
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import logging

class CompanyRAGSystem:
    """Sistema RAG para documentos de la empresa"""
    
    def __init__(self, openai_api_key: str, docs_path: str = "resources/company_docs"):
        self.openai_api_key = openai_api_key
        self.docs_path = Path(docs_path)
        self.vector_store = None
        self.embeddings = None
        self.llm = None
        self.retriever = None
        self.rag_chain = None
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Inicializar componentes
        self._initialize_components()
        
        # Procesar documentos si existen
        if self._has_documents():
            self._process_documents()
    
    def _initialize_components(self):
        """Inicializa los componentes de LangChain"""
        try:
            self.embeddings = OpenAIEmbeddings(openai_api_key=self.openai_api_key)
            self.llm = ChatOpenAI(
                openai_api_key=self.openai_api_key,
                model="gpt-4o-mini",
                temperature=0.3,
                max_tokens=300
            )
            self.logger.info("Componentes RAG inicializados correctamente")
        except Exception as e:
            self.logger.error(f"Error inicializando componentes RAG: {e}")
    
    def _has_documents(self) -> bool:
        """Verifica si hay documentos PDF o TXT en la carpeta"""
        if not self.docs_path.exists():
            return False
        
        pdf_files = list(self.docs_path.glob("*.pdf"))
        txt_files = list(self.docs_path.glob("*.txt"))
        return len(pdf_files) > 0 or len(txt_files) > 0
    
    def _process_documents(self):
        """Procesa todos los documentos PDF y crea el vector store"""
        try:
            self.logger.info(f"Procesando documentos desde: {self.docs_path}")
            
            # Cargar documentos
            documents = self._load_documents()
            
            if not documents:
                self.logger.warning("No se encontraron documentos para procesar")
                return
            
            # Dividir en chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\n\n", "\n", " ", ""]
            )
            
            splits = text_splitter.split_documents(documents)
            self.logger.info(f"Documentos divididos en {len(splits)} chunks")
            
            # Crear vector store
            self.vector_store = FAISS.from_documents(splits, self.embeddings)
            self.retriever = self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 3}
            )
            
            # Crear chain RAG
            self._create_rag_chain()
            
            self.logger.info("Sistema RAG configurado correctamente")
            
        except Exception as e:
            self.logger.error(f"Error procesando documentos: {e}")
    
    def _load_documents(self) -> List[Document]:
        """Carga todos los documentos PDF y TXT"""
        documents = []
        
        if not self.docs_path.exists():
            self.logger.warning(f"Carpeta de documentos no existe: {self.docs_path}")
            return documents
        
        # Cargar archivos PDF
        pdf_files = list(self.docs_path.glob("*.pdf"))
        for pdf_file in pdf_files:
            try:
                loader = PyPDFLoader(str(pdf_file))
                docs = loader.load()
                
                # Añadir metadata
                for doc in docs:
                    doc.metadata["source_file"] = pdf_file.name
                    doc.metadata["file_path"] = str(pdf_file)
                    doc.metadata["file_type"] = "pdf"
                
                documents.extend(docs)
                self.logger.info(f"Cargado PDF: {pdf_file.name}")
                
            except Exception as e:
                self.logger.error(f"Error cargando PDF {pdf_file.name}: {e}")
        
        # Cargar archivos TXT
        txt_files = list(self.docs_path.glob("*.txt"))
        for txt_file in txt_files:
            try:
                loader = TextLoader(str(txt_file), encoding='utf-8')
                docs = loader.load()
                
                # Añadir metadata
                for doc in docs:
                    doc.metadata["source_file"] = txt_file.name
                    doc.metadata["file_path"] = str(txt_file)
                    doc.metadata["file_type"] = "txt"
                
                documents.extend(docs)
                self.logger.info(f"Cargado TXT: {txt_file.name}")
                
            except Exception as e:
                self.logger.error(f"Error cargando TXT {txt_file.name}: {e}")
        
        return documents
    
    def _create_rag_chain(self):
        """Crea la cadena RAG para consultas"""
        if not self.retriever:
            return
        
        # Prompt para RAG
        rag_prompt = PromptTemplate.from_template(
            """Eres un asistente especializado en información de la empresa de Lucas Benites.
            
            Usa la siguiente información de contexto para responder la pregunta de manera natural y conversacional.
            
            Contexto de la empresa:
            {context}
            
            Pregunta del prospecto:
            {question}
            
            Instrucciones:
            1. Responde de manera natural y conversacional
            2. Usa solo la información del contexto proporcionado
            3. Si no tienes información específica, menciona que puedes consultar más detalles
            4. Mantén un tono profesional pero cercano
            5. Enfócate en beneficios para el prospecto
            
            Respuesta:"""
        )
        
        # Crear chain
        self.rag_chain = (
            {"context": self.retriever, "question": RunnablePassthrough()}
            | rag_prompt
            | self.llm
            | StrOutputParser()
        )
    
    def should_use_rag(self, message: str, intent: str = "") -> bool:
        """Determina si se debe usar RAG para responder"""
        if not self.rag_chain:
            return False
        
        # Palabras clave que indican necesidad de información específica
        rag_triggers = [
            # Servicios y productos
            "servicios", "automatización", "inteligencia artificial", "ia", "chatbot",
            "servicio", "producto", "solución", "tecnología", "software",
            
            # Casos de éxito y experiencia
            "casos", "éxito", "experiencia", "ejemplo", "cliente", "resultados",
            "testimonios", "referencias", "portfolio", "trabajos",
            
            # Información comercial
            "precio", "costo", "presupuesto", "inversión", "paquete", "plan",
            "metodología", "proceso", "tiempo", "plazo", "entrega",
            
            # Información de la empresa
            "lucas", "benites", "empresa", "compañía", "quién", "experiencia",
            "trayectoria", "certificaciones", "especialidad",
            
            # Industrias específicas
            "restaurante", "médico", "dental", "consultorio", "taller", "ecommerce",
            "comercio", "industria", "sector", "rubro",
            
            # Preguntas técnicas
            "cómo", "qué", "cuál", "cuánto", "cuándo", "dónde", "por qué",
            "funciona", "implementa", "desarrollo", "crear", "hacer"
        ]
        
        message_lower = message.lower()
        
        # Verificar si el mensaje contiene triggers
        for trigger in rag_triggers:
            if trigger in message_lower:
                return True
        
        # Verificar intenciones específicas
        rag_intents = [
            "PRODUCT_INQUIRY",
            "TECHNICAL_QUESTION", 
            "PRICE_INQUIRY",
            "CASE_STUDY_REQUEST",
            "COMPANY_INFO_REQUEST"
        ]
        
        return intent in rag_intents
    
    def search_documents(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """Busca documentos relevantes"""
        if not self.vector_store:
            return []
        
        try:
            docs = self.vector_store.similarity_search(query, k=max_results)
            
            results = []
            for doc in docs:
                results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "source": doc.metadata.get("source_file", "unknown")
                })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error en búsqueda: {e}")
            return []
    
    def get_rag_response(self, question: str) -> Optional[str]:
        """Obtiene una respuesta usando RAG"""
        if not self.rag_chain:
            return None
        
        try:
            response = self.rag_chain.invoke(question)
            return response
            
        except Exception as e:
            self.logger.error(f"Error generando respuesta RAG: {e}")
            return None
    
    def get_context_for_question(self, question: str) -> str:
        """Obtiene contexto relevante para una pregunta"""
        if not self.retriever:
            return ""
        
        try:
            docs = self.retriever.invoke(question)
            context = "\n\n".join([doc.page_content for doc in docs])
            return context
            
        except Exception as e:
            self.logger.error(f"Error obteniendo contexto: {e}")
            return ""
    
    def reload_documents(self):
        """Recarga todos los documentos"""
        self.logger.info("Recargando documentos...")
        if self._has_documents():
            self._process_documents()
            self.logger.info("Documentos recargados exitosamente")
        else:
            self.logger.warning("No hay documentos para cargar")
    
    def get_available_documents(self) -> List[str]:
        """Obtiene la lista de documentos disponibles"""
        if not self.docs_path.exists():
            return []
        
        docs = []
        docs.extend([f.name for f in self.docs_path.glob("*.pdf")])
        docs.extend([f.name for f in self.docs_path.glob("*.txt")])
        return docs
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema RAG"""
        stats = {
            "documents_loaded": len(self.get_available_documents()),
            "vector_store_active": self.vector_store is not None,
            "rag_chain_ready": self.rag_chain is not None,
            "docs_path": str(self.docs_path)
        }
        
        if self.vector_store:
            try:
                stats["total_vectors"] = self.vector_store.index.ntotal
            except:
                stats["total_vectors"] = "unknown"
        
        return stats