#!/usr/bin/env python3
"""Restore only a trusted complete backup into empty destinations; no destructive reset."""
import hashlib,json,os,subprocess,sys,tarfile
from pathlib import Path,PurePosixPath
root=Path(__file__).resolve().parents[1];os.chdir(root)
if len(sys.argv)!=2: raise SystemExit('Uso: python3 scripts/restore.py /ruta/respaldo')
p=Path(sys.argv[1]).resolve();m=json.loads((p/'manifest.json').read_text())
required={'database.sql','data.tar.gz','plugins.tar.gz','.env','compose.yaml'}
if m.get('status')!='completed' or set(m.get('sha256',{}))!=required: raise SystemExit('Manifest incompleto')
for name in required:
    with (p/name).open('rb') as f:
        if hashlib.file_digest(f,'sha256').hexdigest()!=m['sha256'][name]: raise SystemExit('Hash incorrecto: '+name)
for name in ['data','plugins']:
    with tarfile.open(p/(name+'.tar.gz')) as tf:
        for member in tf:
            if PurePosixPath(member.name).is_absolute() or '..' in PurePosixPath(member.name).parts or not (member.isfile() or member.isdir()): raise SystemExit('Archivo inseguro: '+member.name)
if not (root/'.env').is_file(): raise SystemExit('Preparar .env del destino según docs/operacion.md')
def dc(*a,**kw): return subprocess.run(['docker','compose',*a],check=True,**kw)
if dc('ps','--status','running','-q','app',capture_output=True,text=True).stdout.strip(): raise SystemExit('Detener app antes de restaurar')
count=dc('exec','-T','db','sh','-c','MYSQL_PWD="$MARIADB_PASSWORD" mariadb -u "$MARIADB_USER" -N -B "$MARIADB_DATABASE" -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE()"',capture_output=True,text=True).stdout.strip()
if count!='0': raise SystemExit('Destino SQL no vacío; se rechaza sobrescribir')
for name in ['data','plugins']:
    found=dc('run','--rm','--no-deps','-T','--entrypoint','find','app','/opt/kimai/var/'+name,'-mindepth','1','-maxdepth','1',capture_output=True,text=True).stdout.strip()
    if found: raise SystemExit('Volumen no vacío: '+name)
with (p/'database.sql').open('rb') as f:
    dc('exec','-T','db','sh','-c','MYSQL_PWD="$MARIADB_PASSWORD" mariadb -u "$MARIADB_USER" "$MARIADB_DATABASE"',stdin=f)
for name in ['data','plugins']:
    with (p/(name+'.tar.gz')).open('rb') as f:
        dc('run','--rm','--no-deps','-T','--entrypoint','tar','app','-xzf','-','-C','/opt/kimai/var/'+name,stdin=f)
print('Restaurado. Iniciar app, revisar logs y ejecutar aceptación. Si hubo fallo parcial, usar destinos nuevos.')
