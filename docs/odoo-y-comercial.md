# Odoo y propuesta comercial
## Modelo de venta
Servicio sugerido: instalación por cliente + configuración de actividades/tarifas/equipos + capacitación + mantenimiento mensual. Dirigido a agencias, consultoras, estudios y soporte técnico que cobran por horas. Vender horas registradas y reportes, con alcance verificable. Cotizar infraestructura, soporte, SLA, copias y licencias adicionales por separado. No se incluyen pasarela de pagos ni cobros automáticos.

Piloto: crear un cliente y proyecto, invitar a dos usuarios, registrar una semana, revisar presupuesto y entregar un reporte al cliente. Medir adopción, horas sin asignación y diferencia entre horas registradas/facturables. No presentar proyecciones de ingresos como resultados reales.

## Traspaso a Odoo
La vía propuesta es exportación nativa Kimai y preparación de importaciones Odoo. No hay sincronización automática instalada. La versión, edición, módulos y permisos del Odoo destino determinan los campos finales; verificar su plantilla de importación antes de ejecutar.

| Kimai | Destino propuesto | Revisión |
|---|---|---|
| Cliente | Contacto/empresa | RUT/email/ID externo, deduplicación |
| Proyecto | Proyecto | Cliente asociado y responsable |
| Actividad | Tarea o categoría | Decidir según módulos del destino |
| Usuario | Empleado/usuario | Mapeo autorizado; no importar claves |
| Registro de tiempo | Parte de horas | Fecha, horas decimales, proyecto, tarea, empleado |
| Tarifa y total | Regla comercial/registro auxiliar | No confundir costo laboral con tarifa de venta |

1. Hacer inventario y exportar todos los registros autorizados con rango de fechas completo. Guardar originales inmutables y conteos; usar API nativa solo si la exportación no trae campos necesarios, con credenciales de alcance mínimo.
2. Crear IDs externos con prefijo `kimai_`; guardar tabla de correspondencias, moneda y zona. Preservar notas/tags que no tengan campo equivalente como datos auxiliares.
3. Importar primero contactos, usuarios/empleados y proyectos; después tareas y horas. Convertir duración a horas decimales (90 min = 1,5 h), respetando formato decimal del importador.
4. Ensayar en Odoo de pruebas con pocos registros; comparar total de horas por usuario/proyecto/mes y cifras monetarias sin redondeos indebidos. Resolver duplicados antes de repetir importación.
5. Fijar fecha de corte, detener escritura en Kimai y ejecutar exportación final. Aprobar conciliación y preservar copia de consulta según contrato.

Los documentos comerciales de Kimai no equivalen a DTE autorizados por el SII. Si se requiere facturación chilena, definir y validar un proveedor/integración específica antes de vender ese alcance.
