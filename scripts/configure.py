#!/usr/bin/env python3
import os,re,secrets,sys
from pathlib import Path
if len(sys.argv)!=4 or not re.fullmatch(r'[a-z][a-z0-9-]{2,39}',sys.argv[1]) or not re.fullmatch(r'(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}',sys.argv[2]) or not re.fullmatch(r'[A-Za-z0-9._+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',sys.argv[3]):
    raise SystemExit('Uso: python3 scripts/configure.py cliente-demo tiempo.tudominio.cl admin@tudominio.cl')
root=Path(__file__).resolve().parents[1]
prefix='hefesto-tiempo-'+sys.argv[1]
values={'COMPOSE_PROJECT_NAME':prefix,'VOLUME_PREFIX':prefix,'APP_SECRET':secrets.token_hex(32),'DB_PASSWORD':secrets.token_hex(32),'DB_ROOT_PASSWORD':secrets.token_hex(32),'ADMINMAIL':sys.argv[3],'ADMINPASS':secrets.token_hex(24),'TRUSTED_HOSTS':'^(localhost|127[.]0[.]0[.]1|'+sys.argv[2].replace('.','[.]')+')$','TRUSTED_PROXIES':'127.0.0.1','MAILER_URL':'null://localhost'}
try: fd=os.open(root/'.env',os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
except FileExistsError: raise SystemExit('.env ya existe; no se modificó.')
with os.fdopen(fd,'w') as f:
    for k,v in values.items(): f.write(k+"='"+v+"'\n")
print('.env creado con permisos 0600. Guardar secretos en un gestor de claves.')
