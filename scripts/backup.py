#!/usr/bin/env python3
"""Respaldo de hefesto-tiempo (Kimai + MariaDB).

Reglas de material sensible:
- El .env nunca se copia en claro: solo env.vars y, si hay receptor age, el
  .env cifrado (env.age).
- Los volumenes `data` y `plugins` contienen material personal (fichas de tiempo, usuarios): viajan cifrados con age o no viajan y el manifiesto lo declara.
Ver docs/CONTRATO-RESPALDO.md.
"""
import datetime
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from respaldo_contrato import (RespaldoError, artefactos_presentes, cifrar_con_age,
                               escribir_manifiesto, ejecutar, exportar_env,
                               marcar_fallido, receptor_age)

SOFTWARE = "hefesto-tiempo"
VERSION = "2.69.0"
DATABASE = "mariadb"
RAIZ = Path(__file__).resolve().parents[1]
os.chdir(RAIZ)
os.umask(0o077)


def dc(*args, **kw):
    return subprocess.run(["docker", "compose", *args], check=True, **kw)


def main():
    if not (RAIZ / ".env").is_file():
        raise RespaldoError("Falta .env: el respaldo necesita el entorno del kit", 5)
    if not dc("ps", "--status", "running", "-q", "app",
              capture_output=True, text=True).stdout.strip():
        raise RespaldoError("app no esta activa en este contexto Compose; "
                            "revisar recurso y proyecto.", 5)
    carpeta = (RAIZ / "backups" /
               datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    carpeta.mkdir(parents=True, mode=0o700)
    meta = {}
    try:
        dc("stop", "app")
        with (carpeta / "database.sql").open("wb") as out:
            dc("exec", "-T", "db", "sh", "-c",
               'MYSQL_PWD="$MARIADB_PASSWORD" mariadb-dump -u "$MARIADB_USER" '
               '--single-transaction --skip-lock-tables --no-tablespaces "$MARIADB_DATABASE"',
               stdout=out)

        receptor = receptor_age()
        if receptor:
            for nombre in ("data", "plugins"):
                cifrar_con_age(
                    lambda flujo, _n=nombre: dc("run", "--rm", "--no-deps", "-T",
                                                "--entrypoint", "tar", "app",
                                                "-czf", "-", "-C", "/opt/kimai/var/" + _n,
                                                ".", stdout=flujo),
                    carpeta / (nombre + ".tar.gz.age"), receptor)
                meta[nombre] = nombre + ".tar.gz.age (cifrado con age)"
        else:
            meta["volumenes"] = ("excluidos: material personal y no hay receptor age "
                                  "configurado")

        meta.update(exportar_env(RAIZ, carpeta))
        if (RAIZ / "compose.yaml").is_file():
            shutil.copy2(RAIZ / "compose.yaml", carpeta / "compose.yaml")

        artefactos = artefactos_presentes(carpeta)
        escribir_manifiesto(carpeta, SOFTWARE, VERSION, DATABASE, artefactos, extra=meta)
    except Exception:
        marcar_fallido(carpeta, SOFTWARE, VERSION, DATABASE)
        raise
    finally:
        dc("start", "app")
    print("Respaldo completo:", carpeta)
    print("El .env no viaja en claro: solo cifrado con age o fuera del respaldo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(ejecutar(main))
