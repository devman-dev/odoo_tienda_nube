# Tienda Nube ⇆ Odoo Connector (Devoo)

Conector de **Tienda Nube** para **Odoo** que permite sincronizar catálogo, categorías, variantes, precios, stock, pedidos, cupones y metadatos comerciales entre ambas plataformas. Incluye **webhooks** para eventos de Tienda Nube, **wizards** de importación/sincronización masiva y un **log centralizado** de eventos.

> Compatibilidad probada en Odoo **15, 16, 17, 18 y 19**

---

## Características principales

- **Autenticación Tienda Nube por Access Token** a nivel compañía (`res.company`):  
  - `tiendanube_access_token` (token) y `tiendanube_id` (store/user id).  
  - Panel de configuración en la ficha de compañía (pestaña **Tienda Nube**).
- **Catálogo de productos**
  - Campos de mapeo en `product.template` y `product.product` (IDs TN, URL pública, “Mostrar en tienda”, “Envío gratis”, categorías TN, precio promocional, stock ilimitado, dimensiones, MPN, grupo etario, género, etc.).
  - **Creación/actualización** de productos/variantes en Tienda Nube desde Odoo.
  - **Sincronización masiva** mediante wizard de “*Mass Synchronize Products*” con acciones para setear y propagar `id_tn` por template/variantes.
  - **Imágenes**: controlador público para servir imágenes escaladas desde Odoo:  
    `GET /ati_tn_product_template_ids/<int:id>`
- **Categorías Tienda Nube**
  - Modelo `category.tn` y asignación Many2many en productos.  
  - Wizard para **importar todas las categorías** desde Tienda Nube y crear en Odoo.
- **Stock**
  - Modo de cálculo configurable: **Stock en mano** vs **Pronosticado** (`tn_config_stock`).  
  - **Tiempo real** (al confirmar movimientos) o **planificado por CRON** (cada 5 minutos por defecto).  
  - Mapeo por almacén (`stock.warehouse.location_id_tn`) para identificar centros de distribución de Tienda Nube.
- **Precios e impuestos**
  - Lista de precios a usar (`tn_pricelist_id`).  
  - Tipo de impuesto en precio: **Incluido** / **No incluido** (`tn_type_tax`).  
  - Sincroniza **precio normal** y **precio promocional** cuando corresponda.
- **Pedidos / Eventos**
  - **Webhooks** de Tienda Nube (orders/products/categories, etc.) con **deduplicación** por ventana de 3 segundos y **locking** preventivo para evitar procesamientos en paralelo.  
  - Controlador público: `POST /webhook_tn/<string:code_event>`.
- **Cupones**
  - Modelo `coupon.tn` con tipos, fechas, usos, categorías y flags asociados.
- **Logs**
  - Modelo `tn.log` y vistas (lista/form) con decoraciones por nivel (info/warning/error/success).
- **Herramientas de administración (Wizards)**
  - Importar **productos**, **categorías**, **pedidos**, **cupones** desde Tienda Nube a Odoo.  
  - Obtener **ubicaciones (locations) TN** y enlazarlas con almacenes Odoo.  
  - **Sincronización masiva** de productos/variantes.

> Dependencias Odoo: `base`, `stock`, `sale_management`.  
> Dependencias Python: `requests`, `Pillow` (para manejo de imágenes).

---

## Arquitectura

```
odoo_tienda_nube/
├── controllers/
│   ├── get_image_product_template_ids.py   # Servir imágenes de productos
│   └── webhook_tiendanube.py               # Endpoint de Webhooks + dedupe/locking
├── models/
│   ├── res_company_inherit.py              # Configuración + métodos core de sync TN
│   ├── product_template_inherit.py         # Campos TN en template
│   ├── product_product_inherit.py          # Campos TN en variante
│   ├── category_tn.py                      # Categorías TN (M2M en productos)
│   ├── sale_order_inherit.py               # Ajustes de ventas cuando aplica
│   ├── stock_move_line_inherit.py          # Hook para stock realtime
│   ├── stock_warehouse_inherit.py          # location_id_tn por almacén
│   ├── webhook_tn.py                       # Definición/gestión de webhooks TN
│   ├── coupon_tn.py                        # Cupones TN
│   └── tn_log.py                           # Logging unificado
├── wizards/
│   ├── create_all_*_odoo.py                # Import masivo (productos/categorías/…)
│   ├── synchronize_products_wizard.py
│   └── mass_synchronize_products_wizard.py
├── views/                                  # Vistas, menús y acciones
├── data/                                   # CRON de stock, acciones técnicas
├── security/                               # Reglas y accesos
├── static/                                 # Assets backend (CSS wizard)
├── __manifest__.py
└── __init__.py
```

---

## Instalación

1. **Requisitos**
   - Odoo 15/16/17/18/19 (instalar la versión del módulo correspondiente a tu versión).
   - Python: `requests`, `Pillow`.
   - Usuario con permisos de configuración en Odoo.

2. **Cargar el módulo** en la carpeta de addons y **actualizar lista de aplicaciones**.  
3. **Instalar** “Tienda Nube – Odoo Connector”.

---

## Configuración

1. **Compañía** → pestaña **Tienda Nube**:
   - `tiendanube_access_token`: Token de API (Bearer) provisto por Tienda Nube.  
   - `tiendanube_id`: ID de tienda/usuario.  
   - `tn_pricelist_id`: Lista de precios para sincronización.  
   - `tn_type_tax`: Tipo de impuesto en precio (**incluido** / **no incluido**).  
   - **Stock**:  
     - `tn_config_stock`: *stock* vs *stock-price* (pronosticado).  
     - `tn_config_stock_realtime`: activar si querés actualización instantánea.
   - **Campos a sincronizar** (flags por nombre/categorías/precio promocional/dimensiones/sku/mpn/age group/género/costo/descripción/publicado/envío gratis, etc.).

2. **Almacenes** (`stock.warehouse`):  
   - Completar `location_id_tn` con el **ID de Centro de Distribución** de Tienda Nube (podés obtenerlos con el wizard **Get TN Locations**).

3. **CRON de stock** (si *no* usás realtime):  
   - Job “**Actualizar Stock Tienda Nube**” corre cada **5 min** por defecto (`data/cron_update_stock_tn.xml`). Ajustar si es necesario.

4. **Webhooks (opcional pero recomendado)**:  
   - Crear en Tienda Nube los webhooks de **categories/products/orders** apuntando a:  
     `POST https://TU_DOMINIO/webhook_tn/<code_event>`  
   - El módulo implementa **deduplicación ~3s** y bloqueo de ejecución para evitar reprocesos.

---

## Uso típico

- **Importar catálogo inicial**: wizards “Create All Categories/Products/Orders/Coupons in Odoo”.  
- **Sincronizar masivamente**: wizard **Mass Synchronize Products** (set/propaga `id_tn`, precios, flags).  
- **Actualizar stock**: automático vía **realtime** o **CRON** (según configuración).  
- **Monitoreo**: menú de **Logs** (`tn.log`) para revisar mensajes y errores.  
- **Imágenes**: `GET /ati_tn_product_template_ids/<int:id>` sirve la imagen 1920 del producto por ID de variante.

---

## Seguridad y permisos

- Reglas y accesos incluidos en `security/`. Asegurate de asignar permisos a los grupos que van a operar con el conector (administradores funcionales y operativos).

---

## Buenas prácticas y notas

- **Listas de precios**: definí correctamente tarifas e impuestos para evitar desfasajes con `tn_type_tax`.  
- **Warehouses/locations**: sin `location_id_tn` no se actualiza stock en Tienda Nube.  
- **Productos con múltiples variantes**: el wizard de sincronización gestiona **`id_tn`** por **template** y por **variante**.  
- **Webhooks**: si tu tienda TN emite múltiples eventos juntos, la deduplicación y el lock evitan procesamientos duplicados.  
- **Imágenes**: el endpoint público sirve binario con `Content-Type` dinámico detectado.

---

## Endpoints

- **Webhooks**: `POST /webhook_tn/<string:code_event>` – procesa eventos TN con deduplicación.  
- **Imágenes**: `GET /ati_tn_product_template_ids/<int:id>` – devuelve la imagen del `product.product` (`image_1920`).

---

## Troubleshooting

- **Stock no se actualiza**: revisar `location_id_tn` en cada almacén, flags de realtime/cron y permisos del token.  
- **Precios incorrectos**: confirmar `tn_pricelist_id` y `tn_type_tax`.  
- **Webhooks repetidos**: verificar que el emisor no reintente; el conector deduplica por ~3s.  
- **Errores de API**: ver el menú de **Logs** (modelo `tn.log`) y el log del servidor Odoo.

---

## Roadmap corto

- Page en Notebook de product para unificar botones y caracteristicas para TN
- Facturacion y Pagos automaticos de ventas en TN a Odoo

---

## Créditos

- **Devoo** — Implementación y mantenimiento.
- Sitio web: https://devoo.io

