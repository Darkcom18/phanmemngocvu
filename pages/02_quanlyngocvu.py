# pages/02_quanlyngocvu.py
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
from datetime import datetime, date
from utils.gs import read_df, write_df, options, add_lookup

# ---- Date helpers ----
DATE_FMT_SAVE = "%d-%m-%Y"  # dd-mm-yyyy

def parse_any_date(s):
    if pd.isna(s):
        return pd.NaT
    if isinstance(s, (datetime, date)):
        return pd.to_datetime(s)
    s = str(s).strip()
    for fmt in ["%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"]:
        try:
            return pd.to_datetime(s, format=fmt, dayfirst=True)
        except Exception:
            pass
    return pd.to_datetime(s, dayfirst=True, errors="coerce")

def fmt_date(d):
    if pd.isna(d): return ""
    if isinstance(d, (pd.Timestamp, datetime, date)):
        return pd.to_datetime(d).strftime(DATE_FMT_SAVE)
    return str(d)

def ensure_numeric_cols(df, cols):
    # Tạo cột nếu thiếu, rồi ép numeric (Series, không phải scalar)
    for colname in cols:
        if colname not in df.columns:
            df[colname] = 0
        df[colname] = pd.to_numeric(df[colname], errors="coerce").fillna(0.0)
    return df

st.set_page_config(page_title="quanlyngocvu", layout="wide")
st.title("Quản lý Ngọc Vũ")

tab1, tab2, tab3, tab4 = st.tabs(
    ["Thống kê doanh thu", "Đối chiếu tồn kho", "Lương & Hoa hồng", "Danh mục/Thiết lập"]
)

# =======================
# TAB 1: Thống kê doanh thu
# =======================
with tab1:
    st.subheader("Báo cáo theo ngày/tuần (2-CN)/tháng")
    gran = st.selectbox("Nhóm theo", ["Ngày","Tuần (2-CN)","Tháng"], key="rpt_gran")
    data_src = st.multiselect("Nguồn", ["XE_MAY","OTO"], default=["XE_MAY","OTO"], key="rpt_src")

    dfs = []
    for src in data_src:
        try:
            dfi = read_df(src)
            if dfi.empty:
                continue
            dfi["Nguồn"] = src
            dfs.append(dfi)
        except Exception:
            pass

    if dfs:
        df = pd.concat(dfs, ignore_index=True)
        df["Ngày"] = df["Ngày"].apply(parse_any_date)
        df = df.dropna(subset=["Ngày"])

        def to_float(x):
            try:
                return float(str(x).replace(",", ""))
            except Exception:
                return 0.0

        def revenue_row(r):
            if r["Nguồn"] == "OTO":
                sl = to_float(r.get("Số lượng", 0))
                dg = to_float(r.get("Đơn giá", 0))
                tt = to_float(r.get("Thanh Toán", 0))
                return sl * dg if (sl * dg) > 0 else tt
            else:
                return to_float(r.get("Thanh Toán", 0))

        df["Doanh thu"] = df.apply(revenue_row, axis=1)

        if gran == "Ngày":
            grp = df.groupby(df["Ngày"].dt.date)["Doanh thu"].sum().reset_index(name="Doanh thu")
        elif gran == "Tháng":
            grp = df.groupby([df["Ngày"].dt.to_period("M").dt.to_timestamp()])["Doanh thu"].sum().reset_index(name="Doanh thu")
        else:
            df["Thứ"] = df["Ngày"].dt.dayofweek
            df["Ngày_thu2"] = df["Ngày"] - pd.to_timedelta(df["Thứ"], unit="D")
            grp = df.groupby(df["Ngày_thu2"].dt.date)["Doanh thu"].sum().reset_index(name="Doanh thu")

        grp.rename(columns={grp.columns[0]: "Mốc"}, inplace=True)
        grp["Mốc"] = pd.to_datetime(grp["Mốc"]).dt.strftime(DATE_FMT_SAVE)

        st.dataframe(grp, use_container_width=True)
        st.bar_chart(grp.set_index("Mốc")["Doanh thu"])
    else:
        st.info("Chưa có dữ liệu doanh thu.")

# =======================
# TAB 2: Đối chiếu tồn kho
# =======================
with tab2:
    st.subheader("So sánh tồn kho & giao hàng (kể cả vỏ bình)")
    try:
        inv = read_df("INVENTORY")
    except Exception:
        inv = pd.DataFrame(columns=["Mặt hàng","Tồn đầu","Nhập","Xuất","Tồn cuối","Ghi chú"])

    def sum_qty(ws, qty_col):
        try:
            dfq = read_df(ws)
            if dfq.empty:
                return pd.Series(dtype=float)
            dfq["Ngày"] = dfq["Ngày"].apply(parse_any_date)
            dfq = dfq.dropna(subset=["Ngày"])
            key = "Loại sản phẩm" if "Loại sản phẩm" in dfq.columns else None
            if key is None:
                return pd.Series(dtype=float)
            return pd.to_numeric(dfq.get(qty_col, 0), errors="coerce").groupby(dfq[key]).sum()
        except Exception:
            return pd.Series(dtype=float)

    x1 = sum_qty("XE_MAY", "Số lượng giao")
    x2 = sum_qty("OTO", "Số lượng")
    out = (x1.add(x2, fill_value=0)).reset_index()
    if not out.empty:
        out.columns = ["Mặt hàng", "Xuất_tính_từ_đơn"]

    if not inv.empty and not out.empty:
        inv_agg = inv.merge(out, on="Mặt hàng", how="left")
        inv_agg["Xuất"] = pd.to_numeric(inv_agg.get("Xuất", 0), errors="coerce").fillna(0)
        inv_agg["Xuất_tính_từ_đơn"] = pd.to_numeric(inv_agg.get("Xuất_tính_từ_đơn", 0), errors="coerce").fillna(0)
        inv_agg["Chênh lệch (Xuất_tính - Xuất)"] = inv_agg["Xuất_tính_từ_đơn"] - inv_agg["Xuất"]
        st.dataframe(inv_agg, use_container_width=True)
    else:
        st.info("Thiếu INVENTORY hoặc dữ liệu đơn hàng để đối chiếu.")

    st.caption("Theo dõi vỏ bình: so 'Vỏ về' (XE_MAY) với tab BOTTLE_RETURN để phát hiện thất thoát.")

# =======================
# TAB 3: Lương & Hoa hồng
# =======================
with tab3:
    st.subheader("Tính lương theo công & hoa hồng theo doanh thu giao")
    thang = st.text_input("Tháng (mm/YYYY)", value=pd.Timestamp.today().strftime("%m/%Y"), key="pay_month")

    # Điểm danh (CONG)
    try:
        cong = read_df("CONG")
        if cong.empty:
            cong = pd.DataFrame(columns=["Ngày","Nhân viên","Ca","Công","Ghi chú"])
        else:
            cong["Ngày"] = cong["Ngày"].apply(parse_any_date)
            cong = cong[cong["Ngày"].dt.strftime("%m/%Y") == thang]
    except Exception:
        cong = pd.DataFrame(columns=["Ngày","Nhân viên","Ca","Công","Ghi chú"])

    # Tổng công theo nhân viên
    if not cong.empty and "Công" in cong.columns:
        cong["Công"] = pd.to_numeric(cong["Công"], errors="coerce").fillna(0.0)
        tong_cong = cong.groupby("Nhân viên")["Công"].sum().reset_index(name="Công")
    else:
        tong_cong = pd.DataFrame(columns=["Nhân viên","Công"])

    # Doanh thu theo người chở (XE_MAY)
    try:
        xm = read_df("XE_MAY")
        if xm.empty:
            hh_xm = pd.DataFrame(columns=["Nhân viên","Doanh thu"])
        else:
            xm["Ngày"] = xm["Ngày"].apply(parse_any_date)
            xm = xm[xm["Ngày"].dt.strftime("%m/%Y") == thang]
            xm["TT"] = pd.to_numeric(xm.get("Thanh Toán", 0), errors="coerce").fillna(0)
            hh_xm = xm.groupby("Người chở")["TT"].sum().reset_index()
            hh_xm.columns = ["Nhân viên","Doanh thu"]
    except Exception:
        hh_xm = pd.DataFrame(columns=["Nhân viên","Doanh thu"])

    # Hợp nhất
    df = pd.merge(tong_cong, hh_xm, on="Nhân viên", how="outer")

    # Đảm bảo cột số tồn tại rồi ép numeric (tránh AttributeError)
    df = ensure_numeric_cols(df, ["Công", "Doanh thu", "Tạm ứng", "Khấu trừ"])

    # Tính lương
    df["Lương cơ bản"] = (df["Công"].astype(float) * 250_000).round(0)
    df["Hoa hồng"] = (df["Doanh thu"].astype(float) * 0.02).round(0)
    df["Tổng lương"] = (df["Lương cơ bản"] + df["Hoa hồng"] - df["Tạm ứng"] - df["Khấu trừ"]).round(0)

    # Hiển thị đẹp: int cho các cột tiền
    for mcol in ["Lương cơ bản", "Hoa hồng", "Tổng lương", "Tạm ứng", "Khấu trừ"]:
        df[mcol] = pd.to_numeric(df[mcol], errors="coerce").fillna(0).astype(int)

    df.insert(0, "Tháng", thang)

    st.dataframe(df, use_container_width=True)

    if st.button("Ghi vào LUONG (ghi đè toàn sheet)", key="pay_write"):
        try:
            write_df("LUONG", df)
            st.success("Đã cập nhật LUONG!")
        except Exception as e:
            st.error(f"Lỗi ghi LUONG: {e}")

# =======================
# TAB 4: Danh mục/Thiết lập
# =======================
with tab4:
    st.subheader("Quản lý danh mục & gợi ý nhập liệu")
    st.caption("Thêm nhanh vào LOOKUPS: Đường, Loại sản phẩm, Loại bình, PP Thanh toán, Người chở, Mặt hàng.")
    col1, col2 = st.columns(2)

    with col1:
        kind = st.selectbox("Loại danh mục", ["Đường","Loại sản phẩm","Loại bình","PP Thanh toán","Người chở","Mặt hàng"], key="lk_kind")
        value = st.text_input("Giá trị thêm", key="lk_value")
        if st.button("Thêm vào LOOKUPS", key="lk_add"):
            if value.strip():
                add_lookup(kind, value.strip())
                st.success("Đã thêm!")

    with col2:
        try:
            lk = read_df("LOOKUPS")
            if not lk.empty:
                st.dataframe(lk.sort_values(by=["Loại","Giá trị"]), use_container_width=True, height=400)
            else:
                st.info("LOOKUPS chưa có dữ liệu.")
        except Exception as e:
            st.warning(f"Không đọc được LOOKUPS: {e}")
