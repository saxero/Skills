---
name: generar-certificado
description: Genera certificados en PDF para asistentes a charlas, rellenando un template con datos personalizados
---

# Skill: Generar Certificados en PDF

## Descripción

Esta skill permite generar certificados en PDF de forma automatizada. A partir de un template de PDF que contiene un formulario con tres campos:
- **Nombre del asistente**
- **Título de la charla**
- **Fecha de la charla**

El skill rellena estos datos en el template y genera un PDF final donde **ningún campo del formulario es editable**.

## Requisitos Previos

- Template PDF con formulario requerido y fondo en color blanco donde se colocarán los datos a rellenar
- Datos del certificado a generar (nombre, título, fecha)

## Características

✅ Utiliza template PDF existente como base  
✅ Rellena campos de formulario automáticamente  
✅ Bloquea campos para que no sean editables  
✅ Genera uno o múltiples certificados  
✅ Salida clara en formato PDF

## Cómo Usar Esta Skill

### Paso 1: Proporcione el Template de PDF
Suba o proporcione el template del certificado que contiene los campos:
- Campo para: Nombre del asistente
- Campo para: Título del evento/charla
- Campo para: Fecha del evento

### Paso 2: Genere el Certificado
Proporcione la información:
```
nombre: Juan García
titulo_evento: "Python Avanzado"
fecha: "25 de marzo de 2026"
```

### Paso 3: Archivo de Salida
Se generará un PDF `certificado_[nombre].pdf` con los datos completados y bloqueados.

## Implementación Técnica

La skill usa:
- **PyPDF2**: Para manipular el PDF base
- **reportlab**: Para rellenar campos de formulario
- **pdfrw**: Como alternativa para trabajar con AcroForms

### Sustitución de AcroForms/Banderas de Campo

En la implementación actual de nuestro proceso de generación de PDF usando PyMuPDF, utilizamos una estrategia de sustitución de marcadores de posición para gestionar los campos del formulario. Los marcadores de posición de campos en nuestros templates se representan usando[...]

### Campos Editables

Es importante destacar que los campos no son editables en el PDF generado. Esto se debe a que el texto se integra efectivamente en el PDF durante el proceso de generación, resultando en una salida estática que[...]

## Detalles de Implementación

Las especificidades de la implementación se encapsulan en el script `generar_certificado.py`. Este script orquesta la sustitución de marcadores de posición con valores reales, siguiendo la estructura fija definida en[...]

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

## Notas Importantes

- El template debe tener nombres específicos para los campos del formulario
- Se recomienda usar Adobe Reader para crear el template con los campos correctos
- El bloqueo se aplica después de rellenar para mantener integridad de datos
