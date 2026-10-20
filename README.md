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

## Despliegue en Coolify (MVP Hefesto)
Coolify detecta este directorio como recurso Docker Compose y enruta el dominio HTTPS mediante Traefik. La rama `coolify` está ajustada a ese contrato; en concreto:

- El compose **no fuerza nombre de proyecto, red ni volumen** a nivel raíz: Coolify los nombra por recurso.
- Los volúmenes nombrados usan prefijo variable con valor por defecto `hefesto-tiempo`. Si comparte VPS, cámbielo (`VOLUME_PREFIX`) para no colisionar con otra instalación.
- `TRUSTED_PROXIES` admite por defecto las subredes privadas típicas en las que Coolify/Traefik puede asignar su red (`127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16`). Inspeccione la red del contenedor con `docker network inspect <coolify-net>` y ajuste el CIDR a la subred real de Traefik si difiere. Manténgalo estrecho.
- `TRUSTED_HOSTS` debe contener el dominio real (regex) además de `localhost` y `127.0.0.1` para que el healthcheck siga funcionando.
- El admin inicial solo se crea combinando `-f compose.bootstrap.yaml` con `ADMINMAIL` y `ADMINPASS`. **No** use ese compose en producción: publica el puerto 8001. Tras el primer arranque, recree el servicio solo con `compose.yaml` y borre `ADMINPASS` del entorno.
- MariaDB no publica puertos; el acceso es solo por la red interna del compose. SMTP opcional: déjelo en `null://localhost` mientras no haya un proveedor real.

Consulte `.env.example` para la lista completa de variables con su descripción. `docs/despliegue.md` detalla la operación y la aceptación del VPS.

## Stack y límites
Kimai declara soporte para MariaDB/MySQL; Supabase PostgreSQL no es backend nativo compatible. No se incluye Supabase Auth/Storage ni un puente artificial de base de datos. Para Odoo se incluye un procedimiento de exportación y mapeo, no un conector sincronizado.

Correo desactivado por defecto mediante `null://localhost`: los mensajes no se entregan ni quedan en una cola recuperable. Configurar SMTP y probarlo antes de ofrecer recuperación de contraseña por correo. No incluye pagos, integración SII, documentos tributarios electrónicos, plugins de pago ni aplicación móvil personalizada.

Estado: paquete revisado estáticamente; no desplegado, no conectado a cuentas reales y no probado ejecutando Docker en este entorno. La aceptación del VPS sigue pendiente. El ZIP contiene recetas y scripts; las imágenes y el código upstream se descargan al desplegar.
