# MiPresupuesto

Sistema de gestión y análisis de finanzas personales desarrollado en Python como entrega final de laboratorio de programación.

## Descripción

**MiPresupuesto** es una aplicación web que permite registrar ingresos y gastos, consultar el historial de movimientos, establecer presupuestos mensuales por categoría y visualizar indicadores financieros. La moneda utilizada es el **peso dominicano (RD$)** y toda la interfaz está en español.

Los datos son ficticios o introducidos por el usuario. No se emplean datos bancarios reales ni información personal sensible.

## Problema

Muchas personas necesitan una forma sencilla de organizar sus movimientos financieros para observar cuánto ingresan, cuánto gastan y cómo se compara el gasto con un límite mensual. Las hojas de cálculo permiten hacerlo, pero no siempre ofrecen una interfaz clara, validaciones ni visualizaciones listas para analizar.

## Objetivo general

Desarrollar una aplicación web en Python que facilite el registro, la consulta y el análisis de finanzas personales mediante persistencia en CSV, cálculos reproducibles y visualizaciones interactivas.

## Objetivos específicos

- Registrar ingresos y gastos con validación de campos.
- Consultar, filtrar, editar y eliminar movimientos.
- Calcular indicadores: ingresos, gastos, balance y porcentaje de ingresos utilizados.
- Definir presupuestos mensuales por categoría y compararlos con el gasto real.
- Visualizar la información con gráficos de Plotly.
- Permitir la descarga de los datos filtrados.
- Documentar el análisis de datos en un notebook de Jupyter.
- Verificar la lógica de negocio con pruebas automatizadas de pytest.

## Funcionalidades

- Dashboard con indicadores y gráficos.
- Formulario de ingresos.
- Formulario de gastos.
- Historial de movimientos con filtros, ordenamiento, edición y eliminación.
- Presupuesto por categoría con estado visual (dentro del límite, cerca del límite o excedido).
- Página de análisis financiero.
- Exportación a CSV y Excel.
- Datos de demostración ficticios para la primera ejecución.

## Tecnologías utilizadas

| Tecnología | Uso |
| --- | --- |
| Python 3 | Lenguaje principal |
| Streamlit | Interfaz web |
| Pandas | Manipulación y análisis de datos |
| Plotly | Gráficos interactivos |
| Pytest | Pruebas automatizadas |
| CSV | Persistencia de datos |
| openpyxl | Exportación a Excel |
| Jupyter Notebook | Análisis exploratorio |

No se utiliza Flask, Django, bases de datos externas, APIs bancarias, autenticación ni inteligencia artificial.

## Arquitectura del proyecto

```text
MiPresupuesto/
├── app.py                      # Interfaz Streamlit
├── requirements.txt
├── README.md
├── .gitignore
├── data/
│   ├── movimientos.csv
│   └── presupuestos.csv
├── modules/
│   ├── data_manager.py         # Lectura y escritura CSV
│   ├── validaciones.py         # Validación de movimientos
│   ├── ingresos.py
│   ├── gastos.py
│   ├── presupuesto.py
│   └── analisis.py             # Indicadores y filtros
├── tests/
│   └── test_funciones.py
└── notebooks/
    └── analisis_financiero.ipynb
```

La lógica de negocio reside en `modules/`. `app.py` se encarga únicamente de la interfaz, la navegación y la presentación de resultados.

## Requisitos

- Python 3.10 o superior (recomendado).
- pip.
- Navegador web.

## Instalación

```bash
git clone <URL_DEL_REPOSITORIO>
cd MiPresupuesto
python -m venv .venv
```

Activación del entorno virtual:

**Windows (PowerShell):**

```bash
.venv\Scripts\Activate.ps1
```

**Windows (cmd):**

```bash
.venv\Scripts\activate.bat
```

**macOS / Linux:**

```bash
source .venv/bin/activate
```

Instalación de dependencias:

```bash
pip install -r requirements.txt
```

## Ejecución

Desde la raíz del proyecto:

```bash
streamlit run app.py
```

La aplicación se abrirá en el navegador, normalmente en `http://localhost:8501`.

## Pruebas

```bash
pytest
```

Las pruebas cubren totales, balance, porcentaje utilizado, agrupaciones por categoría, estados de presupuesto, validación de montos y el manejo de un DataFrame vacío.

## Notebook

El archivo `notebooks/analisis_financiero.ipynb` presenta un análisis exploratorio de los movimientos ficticios: lectura de datos, estadísticas descriptivas, totales, agrupaciones, evolución mensual, visualizaciones y conclusiones. Su propósito es evidenciar el uso de Pandas para el análisis, de forma independiente a la interfaz Streamlit.

Para ejecutarlo:

```bash
pip install jupyter
jupyter notebook notebooks/analisis_financiero.ipynb
```

## Despliegue

La aplicación puede publicarse en [Streamlit Community Cloud](https://streamlit.io/cloud) a partir de un repositorio de GitHub:

1. Suba el proyecto a GitHub.
2. Inicie sesión en Streamlit Community Cloud.
3. Cree una aplicación nueva y seleccione el repositorio.
4. Indique `app.py` como archivo principal.
5. Confirme que `requirements.txt` está en la raíz.
6. Despliegue y verifique que los archivos de `data/` se incluyan en el repositorio.

Nota: en un entorno en la nube los CSV pueden reiniciarse según el almacenamiento del servicio. Para una entrega académica local, la persistencia en `data/` es suficiente.

## Autor

Nombre del estudiante: *[Completar]*

Institución: *[Completar]*

Asignatura / laboratorio: *[Completar]*
