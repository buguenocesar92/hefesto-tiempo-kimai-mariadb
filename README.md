# Hefesto Tiempo · Kimai
Kit de despliegue de Kimai nativo 2.69.0 + MariaDB 11.4 para Hefesto/Coolify. No es un clon ni una aplicación reescrita. Incluye Compose, generador de secretos, respaldo, restauración y guías de operación y venta.

Permite trabajar con clientes, proyectos, actividades, cronómetro, horas manuales, tarifas, presupuestos, equipos, reportes y exportaciones mediante las funciones nativas. Configurar idioma español, zona America/Santiago y moneda CLP en Kimai según cada usuario/cliente. Los ejemplos son plantillas para carga manual, no datos ya instalados.

## Inicio
Requiere Linux, Docker Engine + Compose v2, Python 3.11+, DNS y proxy HTTPS. Como punto de partida para un piloto pequeño: 2 vCPU y 4 GB RAM; ajustar con medición real.

```sh
python3 scripts/configure.py cliente-demo tiempo.tudominio.cl admin@tudominio.cl
docker compose -f compose.yaml -f compose.bootstrap.yaml up -d
```

Desde tu computador, abrir un túnel al VPS:
```sh
ssh -L 8001:127.0.0.1:8001 usuario@servidor
```
Acceder a http://localhost:8001. Usuario `admin`; clave inicial ADMINPASS en `.env`. Revisar logs del arranque y versión. Completar las instrucciones de `docs/despliegue.md` antes de publicar.

## Stack y límites
Kimai declara soporte para MariaDB/MySQL; Supabase PostgreSQL no es backend nativo compatible. No se incluye Supabase Auth/Storage ni un puente artificial de base de datos. Para Odoo se incluye un procedimiento de exportación y mapeo, no un conector sincronizado.

Correo desactivado por defecto mediante `null://localhost`: los mensajes no se entregan ni quedan en una cola recuperable. Configurar SMTP y probarlo antes de ofrecer recuperación de contraseña por correo. No incluye pagos, integración SII, documentos tributarios electrónicos, plugins de pago ni aplicación móvil personalizada.

Estado: paquete revisado estáticamente; no desplegado, no conectado a cuentas reales y no probado ejecutando Docker en este entorno. La aceptación del VPS sigue pendiente. El ZIP contiene recetas y scripts; las imágenes y el código upstream se descargan al desplegar.
