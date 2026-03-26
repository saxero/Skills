### Ejemplo de Uso en Python

```python
# Generación de un solo certificado
certificado = Certificado('template.pdf')
certificado.generar('nombre', 'curso', 'fecha')

# Generación de certificados en lote
certificados = Certificado.lote('template.pdf', [{'nombre': 'Alice', 'curso': 'Python', 'fecha': '2022-01-01'}, {'nombre': 'Bob', 'curso': 'Java', 'fecha': '2022-01-02'}])

```

### Implementación Técnica

La implementación utiliza PyMuPDF para realizar la sustitución de texto en los documentos PDF generados. Se maneja la inyección de datos mediante el uso de marcadores de posición en el PDF.

### Configuración de Campos No Editables

Esta sección se refiere a la sustitución de texto en formato de marcadores de posición en lugar de utilizar banderas de campos PDF para indicar la no edición.