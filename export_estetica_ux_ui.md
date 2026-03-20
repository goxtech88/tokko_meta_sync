# Guia de Diseño UX/UI — Modulo Factusol

> Exportado desde el proyecto **Facturador Consolidado** (PyQt6).
> Aplica a cualquier interfaz que interactue con bases de datos Factusol.

---

## 1. Identidad Visual

Estilo **ERP Desktop profesional** inspirado en Factusol. Color primario **Crimson (#B70032)** como acento dominante.

### Principios
- **Claridad**: Informacion legible y organizada
- **Coherencia**: Todos los modulos usan los mismos tokens y componentes
- **Profesionalismo**: Estilo corporativo, sin adornos innecesarios
- **Accesibilidad**: Contraste suficiente entre texto y fondo
- **Sin emojis ni iconos Unicode** en botones, labels ni mensajes. Solo iconos **Lucide** en ribbon.

---

## 2. Paleta de Colores

### Tokens Base

| Token | Hex | Uso |
|---|---|---|
| `CRIMSON` | `#B70032` | Color primario: barras, botones, acentos |
| `CRIMSON_DARK` | `#8C0026` | Hover de botones primarios |
| `CRIMSON_LIGHT` | `#D4003A` | Seleccion activa en navegacion |
| `BG_APP` | `#F3F3F4` | Fondo global de la aplicacion |
| `BG_PANEL` | `#FFFFFF` | Fondo de paneles, tablas, cards |
| `BG_RIBBON` | `#FFFFFF` | Cinta de opciones superior |
| `TEXT_MAIN` | `#333333` | Texto principal |
| `TEXT_SEC` | `#666666` | Labels secundarios, hints |
| `BORDER` | `#D4D4D4` | Bordes generales |
| `BORDER_LIGHT` | `#E0E0E0` | Gridlines de tablas |
| `ROW_ALT` | `#FAFAFA` | Zebra striping (filas alternas) |
| `SEL_ROW` | `#D0E8FF` | Fila seleccionada (azul claro, NUNCA crimson) |
| `SEL_ROW_TEXT` | `#1A1A1A` | Texto de fila seleccionada |

### Colores Semanticos

| Contexto | Color | Uso |
|---|---|---|
| Empresa 1 | `#1565C0` | Badges, stock, etiquetas (azul) |
| Empresa 2 | `#2E7D32` | Badges, stock, etiquetas (verde) |
| Consolidado | `#B70032` | Pendiente (E1-E2), totales |
| Stock positivo | `#1565C0` | Azul |
| Stock negativo | `#B70032` | Crimson |
| Stock cero | `#666666` | Gris atenuado |

### Colores de Estado

| Estado | Color | Peso |
|---|---|---|
| Pendiente | `#E65100` (naranja) | Bold |
| Cobrada / Pagada | `#2E7D32` (verde) | Bold |
| Anulada | `#B71C1C` (rojo) | Bold |

### Estados Internos (auxiliares)

| Token | Color | Uso |
|---|---|---|
| `ST_PAGADO` | `#4CAF50` | Estado pagado |
| `ST_PENDIENTE` | `#FF9800` | Estado pendiente |
| `ST_VENCIDO` | `#F44336` | Estado vencido |

---

## 3. Tipografia

| Propiedad | Valor |
|---|---|
| Familia | `Segoe UI, Tahoma, Arial, sans-serif` |
| 10px | Texto de tabla, labels menores |
| 11px (SM) | Buscadores, status bars, botones, labels |
| 12px (MD) | Texto de inputs, contenido principal, tablas |
| 13px (LG) | Titulos de panel, botones grandes |

### Reglas de Uso
- Titulos de panel: **11pt Bold** con `TEXT_MAIN`
- Texto de tabla: **12px Regular** con `TEXT_MAIN`
- Labels secundarios: **11px** con `TEXT_SEC`
- Totales y montos: **13pt Bold** con `CRIMSON`
- Pesos: Regular (contenido), Bold (headers, estados, titulos, botones primarios)

---

## 4. Componentes

### Tablas (QTableWidget)
- Zebra striping: `setAlternatingRowColors(True)` — alterno `#FAFAFA`
- Seleccion: azul claro `#D0E8FF` (NUNCA crimson) — texto `#1A1A1A`
- Headers: fondo `#ECECEC`, texto bold, sin borde izquierdo
- Filas: alto fijo `20px`
- Scroll vertical libre, nunca horizontal forzado
- Columnas redimensionables (`Interactive`), ultima se estira
- **Sorting**: `setSortingEnabled(True)` — para numeros/fechas: `setData(UserRole, raw_value)`
- **Filtro columna**: click en header abre popup estilo Excel con checkboxes

### Botones ([erp_btn(variant)](file:///d:/OneDrive/JOYLA/Facturador_Consolidado/app/ui/erp_style.py#126-186))

| Variante | Fondo | Color | Borde | Hover |
|---|---|---|---|---|
| `primary` | `#B70032` | blanco, bold | ninguno | `#8C0026` |
| `secondary` | `#ECECEC` | `#333333` | `#D4D4D4` | `#DCDCDC` |
| `danger` | `#D32F2F` | blanco | ninguno | `#B71C1C` |
| `ghost` | transparente | `#333333` | `#D4D4D4` | `#EBEBEB` |

- Alto: `28px` (toolbar), `32px` (accion principal), `44px` (boton grande)
- Padding: `4px 12px` minimo
- Disabled: fondo `#CCC`, texto `#888`
- Border-radius: `2px`

### Inputs (QLineEdit, QSpinBox, QDateEdit)
- Alto: `26px`–`28px`
- Borde: `1px solid #D4D4D4`, border-radius `2px`
- Focus: borde cambia a `CRIMSON`
- Padding: `3px 6px`

### Buscadores
- Ancho fijo: `240px`–`260px`
- Placeholder descriptivo: "Buscar codigo, cliente, serie..."
- Focus: borde crimson
- Debounce: `280–300ms`
- Boton limpiar: `X` pegado al lado, `22x22`

### ComboBox
- Mismo estilo que inputs
- Dropdown: fondo blanco, seleccion crimson con texto blanco

### GroupBox
- Titulo en CRIMSON
- Borde gris con border-radius `3px`
- `margin-top: 8px`, `padding-top: 8px`

---

## 5. Patrones de Layout

### Panel Estandar

```
+----------------------------------------------+
| Toolbar (40-44px) [Titulo | Buscar | Acciones]|  <- fondo BG_PANEL, border-bottom BORDER
+----------------------------------------------+
| DateSegmenter (34px) [Presets | Desde/Hasta] |
+----------------------------------------------+
|                                              |
|         Tabla (solo 50 filas visibles)       |
|                                              |
+----------------------------------------------+
| PaginationBar  [|<< < Pag 1/7 > >>| 1-50/340]|
+----------------------------------------------+
| Status bar  [340 facturas]  [hint derecho]   |  <- 11px, TEXT_SEC
+----------------------------------------------+
```

### Toolbars
- Alto: `40px`–`44px`
- Fondo: `BG_PANEL` (#FFFFFF)
- Borde inferior: `1px solid BORDER`
- Layout: `QHBoxLayout` con margins [(8-10, 0, 8-10, 0)](file:///d:/OneDrive/JOYLA/Facturador_Consolidado/app/ui/erp_style.py#10-43)
- Separadores: `QFrame.VLine`, alto `20px`–`22px`, color `BORDER`

### Header Rojo (Editor/Dialogos)
- Barra superior 36-40px con fondo CRIMSON
- Labels: 9px rgba(255,255,255,0.7), valores 11px bold blanco
- Separadores: `QFrame.VLine` rgba(255,255,255,0.3)

### Splitter Vertical (Master-Detail)
- Handle: `background:#E0E0E0; height:3px;`
- Uso: tabla master arriba, detalle abajo

### Splitter Horizontal (Side-by-side)
- Handle: `background:#E0E0E0; width:3px;`
- Uso: paneles lado a lado (ej: Stock + CNS)

---

## 6. Componentes Especializados

### Ribbon (Cinta de Opciones)
- **RibbonTab**: Seleccion de areas funcionales (ej: DOCUMENTOS, SISTEMA)
- **RibbonBtn**: Ancho minimo `68px`, alto fijo `64px`
  - Icono: fuente fija (Lucide o similar), 20pt, centrado arriba
  - Texto: `setFixedWidth(64)`, `setWordWrap(True)`, centrado abajo
- **RibbonGroup**: Grupos de botones con separador vertical y titulo descriptivo

### PaginationBar
- Paginacion de 50 registros por pagina
- Botones: `|<< < Pag X de Y > >>|` + info "Mostrando 1-50 de 340"
- Senal: `pageChanged(int)`
- API: `set_total(n)`, `get_page_data(list)`, `reset()`
- **SIEMPRE** resetear al cambiar filtros
- Datos: NUNCA paginar en BD (Access no soporta bien OFFSET). Cargar TODO, paginar en memoria.

### DateSegmenter
- Presets pill-toggle: `HOY | ESTE MES | MES PASADO | ESTE AÑO | TODO`
- Activo: fondo crimson + texto blanco
- Inactivo: fondo `#ECECEC`, hover con borde crimson
- Pills: `border-radius: 12px`
- Rango custom: campos Desde/Hasta (QDateEdit) + boton "Aplicar"
- Senal: `dateFilterChanged(date_from, date_to)`
- Metodo estatico: `filter_by_date(data, key, from, to)` — soporta datetime y date
- Default: "TODO" (sin filtro)

### ColumnFilterManager
- Filtros tipo Excel en headers de tabla
- Se define `filterable` con los campos que permiten filtrado
- Indicador en header cuando hay filtro activo

### Badges de Empresa

```python
def _badge(txt, color):
    l = QLabel(txt)
    l.setStyleSheet(
        f"background:{color}; color:white; border-radius:3px; "
        f"padding:1px 6px; font-size:10px; font-weight:bold;"
    )
    return l

# Empresa 1: azul (#1565C0)
# Empresa 2: verde (#2E7D32)
# Consolidado: crimson (#B70032)
```

---

## 7. Formato de Datos

| Tipo | Funcion | Ejemplo | Descripcion |
|---|---|---|---|
| Precios/Totales | [fmt_precio(val)](file:///d:/OneDrive/JOYLA/Facturador_Consolidado/app/ui/erp_style.py#224-234) | `$ 1,500` | Entero, separador miles, signo $ |
| Stock/Cantidad | [fmt_stock(val)](file:///d:/OneDrive/JOYLA/Facturador_Consolidado/app/ui/erp_style.py#212-222) | `50` | Entero, sin decimales ni separador |
| Porcentajes | [fmt_pct(val)](file:///d:/OneDrive/JOYLA/Facturador_Consolidado/app/ui/erp_style.py#236-246) | `10` | Entero, sin decimales |
| Fechas | `.strftime("%d/%m/%Y")` | `10/03/2026` | Formato dia/mes/año |
| Estados | Mapeo dict con color bold | `Pendiente` | Color segun tabla de estados |

> **REGLA**: Nunca usar `:,.2f` ni `:,.4f` directamente. Siempre usar las funciones centralizadas.

---

## 8. Flujo de Datos en Paneles

```
BD (QThread) -> _data (todo)
                 |
        filtro texto (search)
                 |
        filtro fecha (DateSegmenter)
                 |
        filtro columna (ColumnFilterManager)
                 |
            _filtered
                 |
        paginacion (PaginationBar)
                 |
          _fill_table() -> solo 50 filas
```

### Threading (QThread)
- TODA consulta a BD en QThread separado
- Patron: clase con senales `done(list)` y `error(str)`
- Debounce: `QTimer.singleShot` 280-300ms en buscadores
- Guardar referencia: `self._loader = Thread(...)` (evita GC)

---

## 9. Patron Master-Detail para Seleccion

- Usar `currentCellChanged` (NO `currentRowChanged`)
- Signal: [(row, col, old_row, old_col)](file:///d:/OneDrive/JOYLA/Facturador_Consolidado/app/ui/erp_style.py#10-43)
- Lambda: `table.currentCellChanged.connect(lambda row, *_: self._on_selected(row))`

### Master-Master-Detail (Sync)
- Horizontal QSplitter con 3 areas:
  1. **Izquierda**: Tabla origen con checkboxes + QComboBox (filtro familia) + buscador
  2. **Centro**: Columna angosta (~140px) con boton "Duplicar" crimson
  3. **Derecha**: Tabla destino para verificar duplicados

---

## 10. Orden de Columnas en Tablas

Flujo obligatorio izquierda a derecha:
1. **Control**: Checkbox (si aplica)
2. **Identificacion**: ID / Serie / Nro documento
3. **Temporal**: Fecha
4. **Identidad**: Codigo entidad + Nombre/Descripcion (siempre juntos)
5. **Cantidad**: Campos de conteo
6. **Financiero**: Precios, Descuentos (DT1, DT2, DT3), Total

> Nunca colocar un monto a la izquierda de una fecha o ID.

---

## 11. Checklist para Nuevos Modulos

- [ ] Colores de [erp_style.py](file:///d:/OneDrive/JOYLA/Facturador_Consolidado/app/ui/erp_style.py) — nunca hardcodeados
- [ ] [erp_table_style()](file:///d:/OneDrive/JOYLA/Facturador_Consolidado/app/ui/erp_style.py#47-85) en toda QTableWidget
- [ ] [erp_btn()](file:///d:/OneDrive/JOYLA/Facturador_Consolidado/app/ui/erp_style.py#126-186) para todos los botones
- [ ] [erp_input_style()](file:///d:/OneDrive/JOYLA/Facturador_Consolidado/app/ui/erp_style.py#87-103) para inputs
- [ ] [erp_groupbox_style()](file:///d:/OneDrive/JOYLA/Facturador_Consolidado/app/ui/erp_style.py#105-124) para groupboxes
- [ ] Formato numeros: [fmt_precio()](file:///d:/OneDrive/JOYLA/Facturador_Consolidado/app/ui/erp_style.py#224-234), [fmt_stock()](file:///d:/OneDrive/JOYLA/Facturador_Consolidado/app/ui/erp_style.py#212-222), [fmt_pct()](file:///d:/OneDrive/JOYLA/Facturador_Consolidado/app/ui/erp_style.py#236-246)
- [ ] QThread para toda consulta BD
- [ ] Debounce 280ms en buscadores
- [ ] PaginationBar en toda tabla de datos
- [ ] DateSegmenter si hay campo fecha
- [ ] Reset paginacion al cambiar filtros
- [ ] Status bar con conteo de registros
- [ ] Sin emojis ni iconos Unicode
