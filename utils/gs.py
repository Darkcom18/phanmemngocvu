# utils/gs.py
import streamlit as st
import pandas as pd
from gspread_dataframe import get_as_dataframe, set_with_dataframe
from .auth import get_spreadsheet
from gspread.exceptions import APIError

REQUIRED_SHEETS = {
    "XE_MAY": ["Ngày","Khách hàng","Code","Đường","Loại sản phẩm","Loại bình","Số lượng giao","Vỏ về","Thanh Toán","PP Thanh toán","Chú thích","Người chở"],
    "OTO": ["Ngày","Khách hàng","Loại sản phẩm","Loại bình","Số lượng","Đơn giá","Thanh Toán","PP Thanh toán","Chú thích","Người chở 1","Người chở 2"],
    "DAILY_CLOSE": ["Ngày","Loại sản phẩm","Tồn cuối","Ghi chú","Người nhập"],
    "NHAP_HANG": ["Ngày","Loại sản phẩm","Số lượng nhập","Đơn giá","Thành tiền","Nhà cung cấp","Ghi chú"],
    "CONG": ["Ngày","Nhân viên","Ca","Công","Ghi chú"],
    "LOOKUPS": ["Loại","Giá trị"],
    "PAY_RULES": ["Tháng","Nhân viên","Luong_co_ban","Don_gia_cong","Phu_cap","Tam_ung","Khau_tru"],
    "COMMISSION_RULES": ["Tháng","Loại sản phẩm","Ty_le_%","Hoa_hong_moi_donvi"],
    "LUONG": ["Tháng","Nhân viên","Công","Lương cơ bản","Phụ cấp","Hoa hồng","Tạm ứng","Khấu trừ","Tổng lương"],
    "INVENTORY": ["Loại sản phẩm","Tồn đầu","Nhập","Xuất","Tồn cuối","Ghi chú"],
}

def _cannot_create_sheet_hint(name: str):
    st.error(
        f"Sheet **{name}** chưa tồn tại và tài khoản dịch vụ không có quyền tạo mới."
        "\n➡️ Vào Google Sheets, tạo sheet với **tên & cột** như sau, rồi bấm **Refresh**:"
    )
    cols = REQUIRED_SHEETS.get(name, [])
    if cols:
        st.code(" | ".join(cols))
    st.stop()

def ensure_ws(name: str, rows: int = 1000, cols: int = 30, headers=None):
    """Tạo worksheet nếu có quyền. Nếu không, báo rõ & dừng an toàn."""
    sh = get_spreadsheet()
    try:
        ws = sh.worksheet(name)
        return ws
    except Exception:
        pass
    try:
        ws = sh.add_worksheet(title=name, rows=rows, cols=cols)
        if headers:
            ws.append_row(headers, value_input_option="USER_ENTERED")
        return ws
    except APIError:
        _cannot_create_sheet_hint(name)

def open_ws(name: str):
    sh = get_spreadsheet()
    try:
        return sh.worksheet(name)
    except Exception:
        # KHÔNG tự động tạo để tránh APIError; caller tự quyết
        return None

def read_df(ws_name: str) -> pd.DataFrame:
    ws = open_ws(ws_name)
    if ws is None:
        # thử tạo nếu có headers định nghĩa
        headers = REQUIRED_SHEETS.get(ws_name)
        if headers:
            ws = ensure_ws(ws_name, headers=headers)
        else:
            _cannot_create_sheet_hint(ws_name)
    df = get_as_dataframe(ws, evaluate_formulas=True, header=0)
    if df is None:
        return pd.DataFrame(columns=REQUIRED_SHEETS.get(ws_name, []))
    df = df.dropna(how="all")
    df.columns = [str(c).strip() for c in df.columns]
    return df

def append_row(ws_name: str, row: list):
    ws = ensure_ws(ws_name, headers=REQUIRED_SHEETS.get(ws_name))
    ws.append_row(row, value_input_option="USER_ENTERED")

def write_df(ws_name: str, df: pd.DataFrame):
    ws = ensure_ws(ws_name, headers=REQUIRED_SHEETS.get(ws_name))
    ws.clear()
    set_with_dataframe(ws, df)

def add_lookup(kind: str, value: str):
    if not value: return
    df = read_df("LOOKUPS")
    if df.empty:
        df = pd.DataFrame(columns=["Loại","Giá trị"])
    mask = (df["Loại"].astype(str)==kind) & (df["Giá trị"].astype(str)==value)
    if not mask.any():
        df = pd.concat([df, pd.DataFrame([{"Loại":kind, "Giá trị":value}])], ignore_index=True)
        write_df("LOOKUPS", df)

def options(kind: str):
    df = read_df("LOOKUPS")
    if df.empty: return []
    vals = df.loc[df["Loại"].astype(str)==kind, "Giá trị"].dropna().astype(str)
    vals = [v.strip() for v in vals if v.strip()]
    return sorted(set(vals))

def items_from_inventory():
    inv = read_df("INVENTORY")
    col = "Loại sản phẩm" if "Loại sản phẩm" in inv.columns else None
    if col:
        return sorted(inv[col].dropna().astype(str).str.strip().unique().tolist())
    return []

def replace_rows_by_date(ws_name: str, date_col: str, date_str: str, new_rows: pd.DataFrame):
    old = read_df(ws_name)
    if old.empty:
        base = new_rows.copy()
    else:
        if date_col in old.columns:
            base = old[old[date_col].astype(str) != str(date_str)].copy()
        else:
            base = old.copy()
        base = pd.concat([base, new_rows], ignore_index=True)
    # reorder columns for stability
    cols = REQUIRED_SHEETS.get(ws_name, list(new_rows.columns))
    for c in new_rows.columns:
        if c not in cols:
            cols.append(c)
    base = base.reindex(columns=cols)
    write_df(ws_name, base)
