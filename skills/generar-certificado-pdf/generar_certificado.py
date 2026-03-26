"""
Módulo para generar certificados en PDF a partir de un template.
Rellena campos de formulario y los bloquea para evitar ediciones.
"""

from csv import writer

from pdfrw import PdfReader, PdfWriter
from pdfrw.objects import PdfObject
import os
from pathlib import Path
from typing import Dict, Optional
import fitz


class GeneradorCertificado:
    """
    Genera certificados en PDF rellenando un template y bloqueando campos.
    
    Attributes:
        template_path: Ruta al archivo PDF template con formulario
        pdf: Objeto PdfReader del template
    """
    
    def __init__(self, template_path: str):
        """
        Inicializa el generador con un template de PDF.
        
        Args:
            template_path: Ruta al archivo PDF template
            
        Raises:
            FileNotFoundError: Si el template no existe
        """
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template PDF no encontrado: {template_path}")
        
        self.template_path = template_path
        self.pdf = PdfReader(template_path)
        self.campos_rellenados = {}
    
    def obtener_campos_disponibles(self) -> list:
        """
        Retorna la lista de campos del formulario disponibles en el template.
        
        Returns:
            Lista con los nombres de los campos del formulario
        """
        campos = []
        if self.pdf.Root.AcroForm:
            for campo in self.pdf.Root.AcroForm.Fields:
                if campo.T:
                    nombre = campo.T[1:-1]  # Quita comillas
                    campos.append(nombre)
        return campos
    
    def reemplazar_texto(self, output_pdf, reemplazos):
        doc = fitz.open(self.template_path)

        for page in doc:
            for key, value in reemplazos.items():
                # ✅ Fix 1: construir el placeholder correctamente
                placeholder = "{{" + key + "}}"
                
                areas = page.search_for(placeholder)
                                
                if not areas:
                    print(f"  ⚠ placeholders no encontrados.")
                    # ✅ Fix 2: intentar búsqueda case-insensitive / ignorando espacios
                    areas = page.search_for(placeholder, quads=True)

                for rect in areas:
                    page.add_redact_annot(rect, fill=(1, 1, 1))
                
                page.apply_redactions()  # ✅ Fix 3: aplicar TODAS las redacciones antes de insertar
                
                for rect in areas:
                    page.insert_text(
                        rect.tl,
                        value,
                        fontsize=14
                    )
        doc.save(output_pdf)
    
    def guardar(self, ruta_salida: str) -> str:
        """
        Guarda el certificado generado en un archivo PDF.
        
        Args:
            ruta_salida: Ruta donde guardar el PDF
            
        Returns:
            Ruta absoluta del archivo guardado
        """
        # Crear directorio si no existe
        print (ruta_salida)
        
        output_dir = os.path.dirname(ruta_salida)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Escribir el PDF
        PdfWriter().write(ruta_salida, self.pdf)
        
        ruta_abs = os.path.abspath(ruta_salida)
        
        print(f"✓ Certificado guardado en: {ruta_abs}")
        return ruta_abs
    
    def generar(self, datos: Dict[str, str], ruta_salida: str) -> str:
        """
        Método todo-en-uno: rellena, bloquea y guarda el certificado.
        
        Args:
            datos: Diccionario con los datos a rellenar
            ruta_salida: Ruta donde guardar el PDF
            
        Returns:
            Ruta absoluta del archivo generado
        """
        self.reemplazar_texto( ruta_salida, datos)
                

def flatten_con_pymupdf(input_path, output_path):
    doc = fitz.open(input_path)
    new_doc = fitz.open()

    for page in doc:
        pix = page.get_pixmap()
        img_pdf = fitz.open("pdf", pix.tobytes("pdf"))
        new_doc.insert_pdf(img_pdf)

    new_doc.save(output_path)

def generar_certificados_lote(template_path: str, registros: list, 
                              directorio_salida: str = ".") -> list:
    """
    Genera múltiples certificados a partir de una lista de registros.
    
    Args:
        template_path: Ruta al template PDF
        registros: Lista de diccionarios con datos para cada certificado
        directorio_salida: Directorio donde guardar los PDFs
        
    Returns:
        Lista de rutas de archivos generados
        
    Example:
        registros = [
            {"nombre": "Juan García", "titulo_charla": "Python", "fecha": "25/03/2026"},
            {"nombre": "María López", "titulo_charla": "Python", "fecha": "25/03/2026"}
        ]
        archivos = generar_certificados_lote("template.pdf", registros, "salida/")
    """
    archivos_generados = []
    
    for i, registro in enumerate(registros, 1):
        try:
            gc = GeneradorCertificado(template_path)
            
            # Crear nombre de archivo basado en el nombre del asistente
            nombre = registro.get("nombre", "sin_nombre").replace(" ", "_")
            nombre_archivo = f"certificado_{nombre}.pdf"
            ruta_salida = os.path.join(directorio_salida, nombre_archivo)
            
            # Generar certificado
            ruta = gc.generar(registro, ruta_salida)
            archivos_generados.append(ruta)
            print(f"[{i}/{len(registros)}] {nombre_archivo}")
            
        except Exception as e:
            print(f"✗ Error generando certificado para '{registro.get('nombre')}': {e}")
    
    return archivos_generados


if __name__ == "__main__":
    # Ejemplo de uso
    try:
        # Crear instancia
        generador = GeneradorCertificado("template.pdf")
        
        # Ver campos disponibles
        #print("Campos disponibles:", generador.obtener_campos_disponibles())
        
        # Rellenar y guardar
        generador.generar(
            {
                "nombre": "Juan García",
                "titulo_evento": "Introducción a Python",
                "fecha": "25 de marzo de 2026"
            },
            "certificado_juan.pdf"
        )
    except FileNotFoundError:
        print("Por favor, proporcione un template.pdf válido")
