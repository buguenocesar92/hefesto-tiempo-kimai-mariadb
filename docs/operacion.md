# Respaldo, recuperación y traspaso
Requisitos de scripts: Python 3.11+, Docker Compose v2 y permisos sobre este recurso. Se ejecutan con el `.env` y el proyecto que realmente ejecutan el servicio. En Coolify localizar el directorio/contexto de su recurso antes de operar. No asumir que una copia independiente del ZIP apunta al mismo recurso.

## Respaldar
```sh
python3 scripts/backup.py
```
Detiene app durante la copia, vuelca SQL con el usuario de aplicación y archiva data/plugins. Copia `.env` y Compose y escribe manifest SHA256 únicamente al completar. Reinicia app incluso si falla; si falla no usar una carpeta sin manifest completo. Los cronómetros nativos se calculan por fechas: pedir detenerlos antes de mantenimiento y comprobar duraciones después.

El respaldo contiene credenciales y datos personales. Cifrar y transferir fuera del VPS mediante la herramienta aprobada del cliente. Conservar, por ejemplo, 7 diarios y 4 semanales según contrato; programar en el VPS una vez medidos duración y espacio. No se ha instalado una tarea programada. Verificar restauración periódicamente. No incluye configuración del proxy, DNS, SMTP externo ni plugins/configuraciones guardados fuera de los volúmenes declarados; archivarlos aparte si se agregan.

## Restaurar en destino nuevo
1. Recuperar backup confiable, ZIP y claves. No modificar la instancia de origen ni borrar sus volúmenes. Probar primero en otro VPS/proyecto.
2. Copiar el `.env` y `compose.yaml` del backup al directorio del kit. Mantener APP_SECRET y claves DB; cambiar COMPOSE_PROJECT_NAME y VOLUME_PREFIX a nombres nuevos. Ajustar dominio/proxy del destino. Usar chmod 600 .env. No compartir sus secretos en tickets.
3. Arrancar solo DB: `docker compose up -d db`. Esperar estado saludable; no arrancar app (migraría la base vacía).
4. Ejecutar `python3 scripts/restore.py /ruta/backup`. Verifica hashes, rechaza rutas peligrosas/enlaces del tar y exige base y volúmenes data/plugins vacíos. Solo acepta respaldos propios y confiables: el SQL es código ejecutable. No hace DROP ni limpia destinos. Un fallo parcial requiere nuevos destinos vacíos.
5. Ejecutar `docker compose up -d app`. Revisar logs, login, clientes, horas, tarifas, archivos y plugins. Completar aceptación. Los usuarios y sus claves vienen de la base restaurada.
6. Hacer el corte final en una ventana: detener escrituras en origen, respaldo final, restaurar en destino nuevo y cambiar DNS/proxy después de verificar. Mantener origen detenido para evitar divergencia. Si se vuelve al origen después de nuevas escrituras en destino, reconciliar primero los cambios.

## Actualizar y entregar
Clonar en un destino de ensayo y restaurar; cambiar imagen Kimai a versión/digest verificados; comprobar migraciones y compatibilidad de plugins. Rollback = restaurar snapshot completo con versión anterior, no ejecutar código viejo sobre base migrada.
Entregar: responsable, dominio, acceso SSH/Coolify, repositorio del kit, versión/digests, volúmenes, fecha de backup, prueba de restauración, accesos en gestor seguro, SMTP, DNS y licencia de cada plugin. Revocar accesos del proveedor saliente al terminar.
