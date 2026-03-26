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

- Template PDF con formulario requerido
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

## Configuración de Campos No Editables

Los campos se bloquean configurando el flag `/Ff` (Field Flags) en el PDF:
- Flag 1 (ReadOnly): Hace el campo de solo lectura
- Flag 4096 (Submit flag): Permite envío de datos

La combinación correcta bloquea el formulario completamente.

## Ejemplo de Uso en Python

```python
from generar_certificado import GeneradorCertificado

gc = GeneradorCertificado("template.pdf")
gc.rellenar_campos({
    "nombre": "María López",
    "titulo_evento": "Data Science con Python",
    "fecha": "25/03/2026"
})
gc.bloquear_formulario()
gc.guardar("certificado_maria_lopez.pdf")
```

## Notas Importantes

- El template debe tener nombres específicos para los campos del formulario
- Se recomienda usar Adobe Reader para crear el template con los campos correctos
- El bloqueo se aplica después de rellenar para mantener integridad de datos
