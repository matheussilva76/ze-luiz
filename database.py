import os
import sqlite3
import json
from datetime import datetime
from pathlib import Path

_default_db = Path("/data/ze_luiz_resultados.db")
DB_PATH = Path(os.getenv("DB_PATH", str(_default_db)))


def _conn():
    return sqlite3.connect(DB_PATH)


def inicializar_db():
    with _conn() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS backtests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rodado_em TEXT NOT NULL,
                ticker TEXT NOT NULL,
                parametros TEXT NOT NULL,
                total_trades INTEGER,
                win_rate REAL,
                lucro_liquido REAL,
                drawdown_maximo REAL,
                mfe_medio REAL,
                mae_medio REAL,
                vol_prevista REAL,
                status_garch TEXT
            )
        """)


def salvar_resultado(
    ticker: str,
    parametros: dict,
    total_trades: int,
    win_rate: float,
    lucro_liquido: float,
    drawdown_maximo: float,
    mfe_medio: float,
    mae_medio: float,
    vol_prevista: float,
    status_garch: str,
):
    with _conn() as con:
        con.execute(
            """
            INSERT INTO backtests
              (rodado_em, ticker, parametros, total_trades, win_rate,
               lucro_liquido, drawdown_maximo, mfe_medio, mae_medio,
               vol_prevista, status_garch)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ticker,
                json.dumps(parametros),
                total_trades,
                round(win_rate, 2),
                round(lucro_liquido, 2),
                round(drawdown_maximo, 2),
                round(mfe_medio, 2),
                round(mae_medio, 2),
                round(vol_prevista, 6),
                status_garch,
            ),
        )


def listar_resultados(limit: int = 50):
    with _conn() as con:
        cur = con.execute(
            """
            SELECT id, rodado_em, ticker, total_trades, win_rate,
                   lucro_liquido, drawdown_maximo, mfe_medio, mae_medio,
                   vol_prevista, status_garch, parametros
            FROM backtests
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def deletar_resultado(id: int):
    with _conn() as con:
        con.execute("DELETE FROM backtests WHERE id = ?", (id,))
