# Changelog — Tienda Nube ⇆ Odoo Connector

## [16.0.6.0.0] - 2026-01-02
### Fixed
- Se modifica algorimo de actualización de precios para evitar el límite de solicitudes de Tienda Nube al realizar actualizaciones masivas.

## [16.0.5.0.0] - 2025-12-16
### Fixed
- Se completa variant_id en sincronización masiva cuando el producto no tiene variantes.

## [16.0.4.0.0] - 2025-12-16
### Added
- Se agrega una línea de venta específica para los envíos.
- Se incorpora un producto de tipo servicio, utilizado automáticamente como concepto de envío.

## [16.0.3.0.0] - 2025-11-10
### Added
- Permite contemplar **imágenes de variantes** tanto en la creación como en la actualización de imágenes en `product.template`, **a elección**.
- **CRON** para la actualización diaria de precios de productos.
- Arreglo en la publicación con más de 8 variantes.
- Asignación automática de código de barras al publicar productos en Tienda Nube.
- Limpieza de logger.
- **Galería de imágenes**: soporte para publicación y actualización de múltiples imágenes por producto.

## [16.0.2.0.0] - 2025-10-13
### Added
- Versión base para Odoo 15/16/17/18.
- Pestaña **Tienda Nube** en `res.company` con:
  - Token/Store ID, lista de precios, tipo de impuesto (incluido/no incluido).
  - Flags de sincronización de campos (nombre, categorías, publicado, envío gratis, SKU/MPN, edad, género, costo, descripción, precio promocional, dimensiones, etc.).
  - Configuración de stock (en mano/pronosticado) y **realtime** vs **CRON**.
- Campos TN en `product.template` y `product.product` (IDs, URL pública, categorías, metadatos comerciales).
- **Wizards** de importación masiva (categorías, productos, pedidos, cupones) y sincronización masiva.
- **Webhooks** con endpoint `/webhook_tn/<code_event>`, **deduplicación ~3s** y locking de ejecución.
- **CRON** “Actualizar Stock Tienda Nube” (cada 5 minutos) y actualización **en tiempo real** opcional.
- Controlador público de **imágenes** `/ati_tn_product_template_ids/<id>`.
- **Logs** (`tn.log`) con decoraciones por nivel en vistas tree/form.

### Changed
- Ajustes en vistas para exponer campos TN en productos, variantes y almacenes (`location_id_tn`).

### Fixed
- Validaciones varias ante configuraciones incompletas (sin almacenes TN, sin token, etc.).

### Security
- …
