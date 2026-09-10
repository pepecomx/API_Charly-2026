"""Read-only MySQL diagnostics. Run with DATABASE_URL configured."""
import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import text
from config.db import engine

parser = argparse.ArgumentParser()
parser.add_argument('--fecha', required=True, help='YYYY-MM-DD, preferably a day known to contain events')
args = parser.parse_args()
start = datetime.strptime(args.fecha, '%Y-%m-%d')
if engine.dialect.name != 'mysql':
    raise SystemExit('Configure DATABASE_URL con mysql+pymysql; eventos requiere MySQL.')
try:
    with engine.connect() as conn:
        row = conn.execute(text('SELECT DATABASE() AS base, @@session.sql_mode AS sql_mode, NOW() AS hora_bd')).mappings().one()
        print(dict(row))
        print('Tabla usuarios accesible:', conn.execute(text('SELECT 1 FROM usuarios LIMIT 1')).first() is not None)
        count = conn.execute(text('SELECT COUNT(*) FROM vision.eventos_vw1 WHERE FechaCreacionLocal >= :inicio AND FechaCreacionLocal < :fin'), {'inicio': start, 'fin': start+timedelta(days=1)}).scalar_one()
        print('Eventos del dia:', count)
except Exception as exc:
    # Avoid printing connection strings or driver error messages containing credentials.
    original = getattr(exc, 'orig', None)
    code = original.args[0] if original and original.args and isinstance(original.args[0], int) else None
    print('Fallo:', type(exc).__name__, 'codigo MySQL:', code)
    print('1045: acceso; 1049: base inexistente; 1146: tabla/vista inexistente; 1142: permisos; 2003: red/puerto.')
    raise SystemExit(1)
finally:
    engine.dispose()
