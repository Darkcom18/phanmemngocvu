# utils/gs.py
import streamlit as st
import pandas as pd
from gspread_dataframe import get_as_dataframe, set_with_dataframe
from .auth import get_spreadsheet

def ensure_ws(name: str, rows: int = 1000, cols: int = 30, headers=None):
    sh = get_spreadsheet()
    try:
        ws = sh.worksheet(name)
    except Exception:
        ws = sh.add_worksheet(title=name, rows=rows, cols=cols)
        if headers:
            ws.append_row(headers, value_input_option="USER_ENTERED")
    return ws

def open_ws(name: str):
    sh = get_spreadsheet()
    try:
        return sh.worksheet(name)
    except Exception:
        return ensure_ws(name)

def read_df(ws_name: str) -> pd.DataFrame:
    ws = open_ws(ws_name)
    df = get_as_dataframe(ws, evaluate_formulas=True, header=0)
    if df is None:
        return pd.DataFrame()
    df = df.dropna(how="all")
    df.columns = [str(c).strip() for c in df.columns]
    return df

def append_row(ws_name: str, row: list):
    ws = ensure_ws(ws_name)
    ws.append_row(row, value_input_option="USER_ENTERED")

def write_df(ws_name: str, df: pd.DataFrame):
    ws = ensure_ws(ws_name)
    ws.clear()
    set_with_dataframe(ws, df)

def add_lookup(kind: str, value: str):
    if not value:
        return
    df = read_df("LOOKUPS")
    if df.empty:
        df = pd.DataFrame(columns=["Loại", "Giá trị"])
    if not ((df["Loại"] == kind) & (df["Giá trị"] == value)).any():
        df = pd.concat([df, pd.DataFrame([{"Loại": kind, "Giá trị": value}])], ignore_index=True)
        write_df("LOOKUPS", df)

def options(kind: str):
    df = read_df("LOOKUPS")
    if df.empty:
        return []
    vals = df.loc[df["Loại"] == kind, "Giá trị"].dropna().astype(str).unique().tolist()
    vals = [v for v in vals if v.strip()]
    return sorted(vals)

def items_from_inventory():
    inv = read_df("INVENTORY")
    if "Mặt hàng" in inv.columns:
        return sorted(inv["Mặt hàng"].dropna().astype(str).unique().tolist())
    return []

def replace_rows_by_date(ws_name: str, date_col: str, date_str: str, new_rows: pd.DataFrame):
    """Ghi đè các dòng có cùng ngày = date_str bằng tập new_rows (đã chuẩn cột)."""
    old = read_df(ws_name)
    if old.empty:
        base = new_rows.copy()
    else:
        if date_col in old.columns:
            mask_keep = old[date_col].astype(str).ne(str(date_str))
            base = old[mask_keep].copy()
        else:
            base = old.copy()
        base = pd.concat([base, new_rows], ignore_index=True)
    # Đảm bảo thứ tự cột ổn định
    cols = list(new_rows.columns)
    for c in base.columns:
        if c not in cols:
            cols.append(c)
    base = base[cols]
    write_df(ws_name, base)
