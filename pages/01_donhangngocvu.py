import streamlit as st
import pandas as pd
from datetime import datetime, date
import pandas as pd

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
from utils.gs import read_df, append_row, options, add_lookup, items_from_inventory

st.set_page_config(page_title="donhangngocvu", layout="wide")
st.title("Đơn hàng Ngọc Vũ")

tab1, tab2, tab3, tab4 = st.tabs(["Nhập đơn hàng", "Bảng/Filter", "Chốt tồn kho ngày", "Điểm danh & Công"])

with tab1:
    st.subheader("Nhập đơn hàng")
    subcol = st.radio("Loại phương tiện", ["Xe máy", "Ô tô"], horizontal=True)
    duong_opts = options("Đường")
    loaisp_opts = sorted(set(options("Loại sản phẩm") + items_from_inventory() + ["nv","pn","AQ500","Aqua 350","Aqua 500","Aqua 1.5l","Aqua 5l","Ocany 350","Ocany 600","Ocany 1.5l","Phú Ninh vòi","Phú Ninh up","Thạch Bích vòi","EDen500","Ion_pro"]))
    loaibinh_opts = options("Loại bình") + ["bình","Bình","thùng"]
    pp_opts = options("PP Thanh toán") + ["Tiền Mặt","Chuyển Khoản","Kí Giấy"]
    shipper_opts = options("Người chở") + ["Pháp"]
    if subcol == "Xe máy":
        with st.form("form_xemay", clear_on_submit=True):
            Ngay = st.date_input("Ngày (dd-mm-yyyy)", pd.Timestamp.today())
            Khach = st.text_input("Khách hàng (hoặc số địa chỉ)")
            Code = st.text_input("Code")
            Duong = st.selectbox("Đường", duong_opts + ["(khác)"] if duong_opts else ["(khác)"])
            if Duong == "(khác)":
                Duong = st.text_input("Nhập tên đường mới")
                if Duong: add_lookup("Đường", Duong)
            LoaiSP = st.selectbox("Loại sản phẩm", loaisp_opts)
            LoaiBinh = st.selectbox("Loại bình", loaibinh_opts)
            SoLuong = st.number_input("Số lượng giao", min_value=0, step=1, value=0)
            VoVe = st.text_input("Vỏ về (số hoặc 'x' nếu không)")
            ThanhToan = st.text_input("Thanh Toán (số tiền)")
            PP = st.selectbox("PP Thanh toán", pp_opts)
            GhiChu = st.text_input("Chú thích")
            NguoiCho = st.selectbox("Người chở", shipper_opts)
            submitted = st.form_submit_button("Lưu đơn (XE_MAY)")
            if submitted:
                append_row("XE_MAY", [fmt_date(Ngay), Khach, Code, Duong, LoaiSP, LoaiBinh, SoLuong, VoVe, ThanhToan, PP, GhiChu, NguoiCho])
                st.success("Đã lưu đơn Xe máy!")
    else:
        with st.form("form_oto", clear_on_submit=True):
            Ngay = st.date_input("Ngày (dd-mm-yyyy)", pd.Timestamp.today())
            Khach = st.text_input("Khách hàng (hoặc số địa chỉ)")
            LoaiSP = st.selectbox("Loại sản phẩm", loaisp_opts)
            LoaiBinh = st.selectbox("Loại bình", loaibinh_opts)
            SoLuong = st.number_input("Số lượng", min_value=0, step=1, value=0)
            DonGia = st.text_input("Đơn giá (số)")
            ThanhToan = st.text_input("Thanh Toán (số tiền)")
            PP = st.selectbox("PP Thanh toán", pp_opts)
            GhiChu = st.text_input("Chú thích")
            NguoiCho1 = st.selectbox("Người chở 1", shipper_opts + [""])
            NguoiCho2 = st.selectbox("Người chở 2", shipper_opts + [""])
            submitted = st.form_submit_button("Lưu đơn (OTO)")
            if submitted:
                append_row("OTO", [fmt_date(Ngay), Khach, LoaiSP, LoaiBinh, SoLuong, DonGia, ThanhToan, PP, GhiChu, NguoiCho1, NguoiCho2])
                st.success("Đã lưu đơn Ô tô!")
with tab2:
    st.subheader("Bảng đơn hàng & Filter theo ngày (dd-mm-yyyy)")
    c1, c2 = st.columns(2)
    with c1:
        mode = st.radio("Nguồn dữ liệu", ["XE_MAY","OTO"], horizontal=True)
    with c2:
        date_from = st.date_input("Từ ngày", pd.Timestamp.today().replace(day=1))
        date_to = st.date_input("Đến ngày", pd.Timestamp.today())
    try:
        df = read_df(mode)
        if df.empty:
            st.info("Chưa có dữ liệu.")
        else:
            df["Ngày"] = df["Ngày"].apply(parse_any_date)
            if date_from:
                df = df[df["Ngày"] >= pd.to_datetime(date_from)]
            if date_to:
                df = df[df["Ngày"] <= pd.to_datetime(date_to)]
            show = df.copy()
            show["Ngày"] = show["Ngày"].apply(fmt_date)
            st.dataframe(show, use_container_width=True)
            if mode == "XE_MAY":
                qty = pd.to_numeric(df.get("Số lượng giao", 0), errors="coerce").fillna(0).sum()
                cash = pd.to_numeric(df.get("Thanh Toán", 0), errors="coerce").fillna(0).sum()
                st.metric("Tổng SL giao", int(qty))
                st.metric("Tổng tiền thu", int(cash))
            else:
                qty = pd.to_numeric(df.get("Số lượng", 0), errors="coerce").fillna(0).sum()
                rev = (pd.to_numeric(df.get("Số lượng", 0), errors="coerce").fillna(0) * pd.to_numeric(df.get("Đơn giá", 0), errors="coerce").fillna(0)).sum()
                paid = pd.to_numeric(df.get("Thanh Toán", 0), errors="coerce").fillna(0).sum()
                st.metric("Tổng SL", int(qty))
                st.metric("Doanh thu (Số lượng*Đơn giá)", int(rev))
                st.metric("Tổng đã thu", int(paid))
    except Exception as e:
        st.warning(f"Không đọc được dữ liệu: {e}")
with tab3:
    st.subheader("Nhập & kiểm tra chốt tồn kho hằng ngày")
    colA, colB = st.columns([1,1])
    with colA:
        ngay_close = st.date_input("Ngày chốt (dd-mm-yyyy)", pd.Timestamp.today())
        items_lookup = sorted(set(items_from_inventory() + options("Mặt hàng")))
        item = st.selectbox("Mặt hàng", items_lookup + ["(thêm mới)"] if items_lookup else ["(thêm mới)"])
        if item == "(thêm mới)":
            item = st.text_input("Nhập tên mặt hàng mới")
            if item:
                add_lookup("Mặt hàng", item)
        ton_cuoi = st.number_input("Tồn cuối (đơn vị)", min_value=0, step=1, value=0)
        ghi_chu = st.text_input("Ghi chú")
        nguoi_nhap = st.text_input("Người nhập", value="")
        if st.button("Lưu chốt tồn"):
            append_row("DAILY_CLOSE", [fmt_date(ngay_close), item, ton_cuoi, ghi_chu, nguoi_nhap])
            st.success("Đã lưu chốt tồn!")
    with colB:
        st.caption("Bảng chốt tồn của ngày đã chọn")
        dfc = read_df("DAILY_CLOSE")
        if not dfc.empty:
            dfc["Ngày"] = dfc["Ngày"].apply(parse_any_date)
            df_show = dfc[dfc["Ngày"].dt.date == pd.to_datetime(ngay_close).date()].copy()
            df_show["Ngày"] = df_show["Ngày"].apply(fmt_date)
            st.dataframe(df_show, use_container_width=True)
        else:
            st.info("Chưa có dữ liệu chốt tồn.")
with tab4:
    st.subheader("Điểm danh nhanh theo ngày")
    today = st.date_input("Ngày (dd-mm-yyyy)", pd.Timestamp.today())
    nhanvien = st.text_input("Nhân viên")
    ca = st.selectbox("Ca", ["Full ngày","Nửa ngày sáng","Nửa ngày chiều"])
    cong = 1.0 if ca=="Full ngày" else 0.5
    ghichu = st.text_input("Ghi chú")
    if st.button("Lưu công"):
        from utils.gs import append_row
        append_row("CONG", [fmt_date(today), nhanvien, ca, cong, ghichu])
        st.success("Đã lưu công!")
