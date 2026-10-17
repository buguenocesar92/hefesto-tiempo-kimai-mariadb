#!/usr/bin/env python3
import datetime,hashlib,json,os,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1];os.chdir(root);os.umask(0o077)
def dc(*a,**kw): return subprocess.run(['docker','compose',*a],check=True,**kw)
if not (root/'.env').is_file(): raise SystemExit('Falta .env')
if not dc('ps','--status','running','-q','app',capture_output=True,text=True).stdout.strip(): raise SystemExit('app no está activa en este proyecto Compose.')
p=root/'backups'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');p.mkdir(parents=True)
try:
    dc('stop','app')
    with (p/'database.sql').open('wb') as f:
        dc('exec','-T','db','sh','-c','MYSQL_PWD="$MARIADB_PASSWORD" mariadb-dump -u "$MARIADB_USER" --single-transaction --skip-lock-tables --no-tablespaces "$MARIADB_DATABASE"',stdout=f)
    for name in ['data','plugins']:
        with (p/(name+'.tar.gz')).open('wb') as f:
            dc('run','--rm','--no-deps','-T','--entrypoint','tar','app','-czf','-','-C','/opt/kimai/var/'+name,'.',stdout=f)
    for name in ['.env','compose.yaml']: (p/name).write_bytes((root/name).read_bytes())
    hashes={}
    for f in p.iterdir():
        with f.open('rb') as stream: hashes[f.name]=hashlib.file_digest(stream,'sha256').hexdigest()
    (p/'manifest.json').write_text(json.dumps({'status':'completed','version':'2.69.0','sha256':hashes},indent=2))
finally: dc('start','app')
print('Respaldo completo:',p,'— contiene claves; cifrar y copiar fuera del VPS.')
