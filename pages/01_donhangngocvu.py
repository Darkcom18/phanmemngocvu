# pages/01_donhangngocvu.py
import os, sys
import streamlit as st
import pandas as pd
from datetime import datetime, date

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.gs import read_df, append_row, options, add_lookup, items_from_inventory, replace_rows_by_date

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

def safe_options(kind, extra=None):
    try:
        base = options(kind) or []
    except Exception:
        base = []
    if extra:
        base = list(base) + list(extra)
    base = [str(x).strip() for x in base if str(x).strip()]
    # unique + sorted
    return sorted(dict.fromkeys(base).keys())

def safe_inventory_items():
    try:
        return items_from_inventory() or []
    except Exception:
        return []

st.set_page_config(page_title="donhangngocvu", layout="wide")
st.title("Đơn hàng Ngọc Vũ")

# ========= Tabs =========
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Nhập đơn hàng",
    "Thống kê",
    "Chốt tồn kho ngày",
    "Điểm danh & Công",
    "Nhập hàng"
])

# ============================================================
# TAB 1: Nhập đơn hàng (bỏ trường Code; mặc định người chở)
# ============================================================
with tab1:
    st.subheader("Nhập đơn hàng")
    subcol = st.radio("Loại phương tiện", ["Xe máy", "Ô tô"], horizontal=True, key="veh_type")

    duong_opts = safe_options("Đường")
    loaisp_opts = safe_options(
        "Loại sản phẩm",
        extra=safe_inventory_items() + ["nv","pn","AQ500","Aqua 350","Aqua 500","Aqua 1.5l","Aqua 5l","Ocany 350","Ocany 600","Ocany 1.5l","Phú Ninh vòi","Phú Ninh up","Thạch Bích vòi","EDen500","Ion_pro"]
    )
    loaibinh_opts = safe_options("Loại bình", extra=["bình","Bình","thùng"])
    pp_opts = safe_options("PP Thanh toán", extra=["Tiền Mặt","Chuyển Khoản","Kí Giấy"])
    shipper_opts = safe_options("Người chở", extra=["Pháp","Sâm","Khoa"])

    if subcol == "Xe máy":
        with st.form("form_xemay", clear_on_submit=True):
            Ngay = st.date_input("Ngày (dd-mm-yyyy)", pd.Timestamp.today(), key="xm_ngay")
            Khach = st.text_input("Khách hàng (hoặc số địa chỉ)", key="xm_khach")
            # BỎ "Code": không hiển thị, ghi rỗng khi lưu
            Duong = st.selectbox("Đường", duong_opts + ["(khác)"] if duong_opts else ["(khác)"], key="xm_duong")
            if Duong == "(khác)":
                duong_new = st.text_input("Nhập tên đường mới", key="xm_duong_new")
                if duong_new:
                    add_lookup("Đường", duong_new)
                    Duong = duong_new
            LoaiSP = st.selectbox("Loại sản phẩm", loaisp_opts, key="xm_loaisp")
            LoaiBinh = st.selectbox("Loại bình", loaibinh_opts, key="xm_loaibinh")
            SoLuong = st.number_input("Số lượng giao", min_value=0, step=1, value=0, key="xm_soluong")
            VoVe = st.text_input("Vỏ về (số hoặc 'x' nếu không)", key="xm_vove")
            ThanhToan = st.text_input("Thanh Toán (số tiền)", key="xm_thanhtoan")
            PP = st.selectbox("PP Thanh toán", pp_opts, key="xm_pp")
            GhiChu = st.text_input("Chú thích", key="xm_ghichu")
            # Mặc định người chở = Pháp (có thể đổi)
            default_ship = "Pháp" if "Pháp" in shipper_opts else (shipper_opts[0] if shipper_opts else "")
            NguoiCho = st.selectbox("Người chở", shipper_opts, index=shipper_opts.index(default_ship) if default_ship in shipper_opts else 0, key="xm_nguoi")
            submitted = st.form_submit_button("Lưu đơn (XE_MAY)", type="primary", use_container_width=True)
            if submitted:
                append_row("XE_MAY", [fmt_date(Ngay), Khach, "", Duong, LoaiSP, LoaiBinh, SoLuong, VoVe, ThanhToan, PP, GhiChu, NguoiCho])
                st.success("Đã lưu đơn Xe máy!")
    else:
        with st.form("form_oto", clear_on_submit=True):
            Ngay = st.date_input("Ngày (dd-mm-yyyy)", pd.Timestamp.today(), key="oto_ngay")
            Khach = st.text_input("Khách hàng (hoặc số địa chỉ)", key="oto_khach")
            LoaiSP = st.selectbox("Loại sản phẩm", loaisp_opts, key="oto_loaisp")
            LoaiBinh = st.selectbox("Loại bình", loaibinh_opts, key="oto_loaibinh")
            SoLuong = st.number_input("Số lượng", min_value=0, step=1, value=0, key="oto_soluong")
            DonGia = st.text_input("Đơn giá (số)", key="oto_dongia")
            ThanhToan = st.text_input("Thanh Toán (số tiền)", key="oto_thanhtoan")
            PP = st.selectbox("PP Thanh toán", pp_opts, key="oto_pp")
            GhiChu = st.text_input("Chú thích", key="oto_ghichu")
            # Mặc định người chở 1 = Sâm, 2 = Khoa (có thể đổi)
            def_idx1 = shipper_opts.index("Sâm") if "Sâm" in shipper_opts else 0
            def_idx2 = shipper_opts.index("Khoa") if "Khoa" in shipper_opts else (1 if len(shipper_opts) > 1 else 0)
            NguoiCho1 = st.selectbox("Người chở 1", shipper_opts + [""], index=def_idx1, key="oto_nguoi1")
            NguoiCho2 = st.selectbox("Người chở 2", shipper_opts + [""], index=def_idx2, key="oto_nguoi2")
            submitted = st.form_submit_button("Lưu đơn (OTO)", type="primary", use_container_width=True)
            if submitted:
                append_row("OTO", [fmt_date(Ngay), Khach, LoaiSP, LoaiBinh, SoLuong, DonGia, ThanhToan, PP, GhiChu, NguoiCho1, NguoiCho2])
                st.success("Đã lưu đơn Ô tô!")

# ============================================================
# TAB 2: Thống kê (lọc KH, Loại SP, PP; hiển thị SL Giao, Vỏ đi, Vỏ về theo ngày)
# ============================================================
with tab2:
    st.subheader("Thống kê đơn hàng theo ngày (dd-mm-yyyy)")

    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        src = st.multiselect("Nguồn", ["XE_MAY","OTO"], default=["XE_MAY","OTO"], key="stat_src")
    with c2:
        date_from = st.date_input("Từ ngày", pd.Timestamp.today().replace(day=1), key="stat_from")
    with c3:
        date_to = st.date_input("Đến ngày", pd.Timestamp.today(), key="stat_to")

    # Tải dữ liệu
    frames = []
    for s in src:
        try:
            d = read_df(s)
            if not d.empty:
                d["Nguồn"] = s
                frames.append(d)
        except Exception:
            pass

    if not frames:
        st.info("Chưa có dữ liệu.")
    else:
        df = pd.concat(frames, ignore_index=True)
        df["Ngày"] = df["Ngày"].apply(parse_any_date)
        df = df.dropna(subset=["Ngày"])
        df = df[(df["Ngày"] >= pd.to_datetime(date_from)) & (df["Ngày"] <= pd.to_datetime(date_to))]

        # Chuẩn hoá cột để filter
        df["Khách"] = df.get("Khách hàng/Địa chỉ", df.get("Khách hàng", ""))
        df["Loại sản phẩm"] = df.get("Loại sản phẩm", "")
        df["PP Thanh toán"] = df.get("PP Thanh toán", "")

        f1, f2, f3 = st.columns(3)
        with f1:
            kh_filter = st.multiselect("Khách hàng", sorted(df["Khách"].dropna().astype(str).unique().tolist()), key="stat_kh")
        with f2:
            lsp_filter = st.multiselect("Loại sản phẩm", sorted(df["Loại sản phẩm"].dropna().astype(str).unique().tolist()), key="stat_lsp")
        with f3:
            pp_filter = st.multiselect("PP Thanh toán", sorted(df["PP Thanh toán"].dropna().astype(str).unique().tolist()), key="stat_pp")

        if kh_filter:
            df = df[df["Khách"].astype(str).isin(kh_filter)]
        if lsp_filter:
            df = df[df["Loại sản phẩm"].astype(str).isin(lsp_filter)]
        if pp_filter:
            df = df[df["PP Thanh toán"].astype(str).isin(pp_filter)]

        # Tính chỉ số
        def to_num(x):
            try:
                return float(str(x).replace(",", ""))
            except:
                return pd.NA

        df["SL_Giao"] = 0.0
        df["Vo_ve"] = 0.0

        mask_xm = df["Nguồn"] == "XE_MAY"
        df.loc[mask_xm, "SL_Giao"] = pd.to_numeric(df.loc[mask_xm, "Số lượng giao"], errors="coerce").fillna(0)
        # Vỏ đi ~ số lượng giao, Vỏ về lấy số nếu có (k ký tự 'x' sẽ thành NaN -> 0)
        df["Vo_di"] = df["SL_Giao"]
        df.loc[mask_xm, "Vo_ve"] = pd.to_numeric(df.loc[mask_xm, "Vỏ về"], errors="coerce").fillna(0)

        mask_oto = df["Nguồn"] == "OTO"
        df.loc[mask_oto, "SL_Giao"] = pd.to_numeric(df.loc[mask_oto, "Số lượng"], errors="coerce").fillna(0)
        # Ô tô: không tính vỏ
        df.loc[mask_oto, ["Vo_di","Vo_ve"]] = 0

        # Group theo ngày
        grp = df.groupby(df["Ngày"].dt.date).agg(
            SL_Giao=("SL_Giao","sum"),
            Vo_di=("Vo_di","sum"),
            Vo_ve=("Vo_ve","sum"),
        ).reset_index().rename(columns={"Ngày":"Mốc"})
        grp["Mốc"] = pd.to_datetime(grp["Mốc"]).dt.strftime(DATE_FMT_SAVE)
        st.dataframe(grp, use_container_width=True)

# ============================================================
# TAB 3: Chốt tồn kho ngày (bảng nhập nhanh theo sản phẩm)
# ============================================================
with tab3:
    st.subheader("Chốt tồn kho theo bảng (điền số trực tiếp)")
    ngay_close = st.date_input("Ngày chốt (dd-mm-yyyy)", pd.Timestamp.today(), key="close_ngay_tbl")
    nguoi_nhap = st.text_input("Người nhập", value="", key="close_user_tbl")

    items = sorted(set(safe_inventory_items() + safe_options("Mặt hàng")))
    if not items:
        st.info("Chưa có danh sách Mặt hàng trong LOOKUPS/INVENTORY.")
    else:
        # Nạp dữ liệu đã có của ngày
        dfc = read_df("DAILY_CLOSE")
        dfc_exists = pd.DataFrame(columns=["Mặt hàng","Tồn cuối","Ghi chú"])
        if not dfc.empty:
            dfc["Ngày"] = dfc["Ngày"].apply(parse_any_date)
            sub = dfc[dfc["Ngày"].dt.date == pd.to_datetime(ngay_close).date()]
            if not sub.empty:
                dfc_exists = sub[["Mặt hàng","Tồn cuối","Ghi chú"]].copy()

        base = pd.DataFrame({"Mặt hàng": items})
        base = base.merge(dfc_exists, on="Mặt hàng", how="left")
        base["Tồn cuối"] = pd.to_numeric(base["Tồn cuối"], errors="coerce").fillna(0).astype(int)
        base["Ghi chú"] = base["Ghi chú"].fillna("")

        edited = st.data_editor(
            base,
            key="close_editor",
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "Mặt hàng": st.column_config.TextColumn(disabled=True),
                "Tồn cuối": st.column_config.NumberColumn(min_value=0, step=1),
                "Ghi chú": st.column_config.TextColumn(),
            }
        )

        if st.button("Lưu chốt tồn (ghi đè ngày chọn)", key="close_save_tbl"):
            out = edited.copy()
            out.insert(0, "Ngày", fmt_date(ngay_close))
            out["Người nhập"] = nguoi_nhap
            replace_rows_by_date("DAILY_CLOSE", "Ngày", fmt_date(ngay_close), out[["Ngày","Mặt hàng","Tồn cuối","Ghi chú","Người nhập"]])
            st.success("Đã lưu chốt tồn cho ngày " + fmt_date(ngay_close))

# ============================================================
# TAB 4: Điểm danh & Công (tick sáng/chiều theo nhân viên)
# ============================================================
with tab4:
    st.subheader("Điểm danh nhanh theo bảng")
    ngay_cong = st.date_input("Ngày (dd-mm-yyyy)", pd.Timestamp.today(), key="cong_ngay_tbl")

    nhanvien_list = safe_options("Nhân viên")
    if not nhanvien_list:
        # fallback từ Người chở
        nhanvien_list = safe_options("Người chở")

    if not nhanvien_list:
        st.info("Thêm danh mục Nhân viên (LOOKUPS) để điểm danh.")
    else:
        # Nạp công đã có của ngày
        cong_df = read_df("CONG")
        existed = pd.DataFrame(columns=["Nhân viên","Sáng","Chiều","Ghi chú"])
        if not cong_df.empty:
            cong_df["Ngày"] = cong_df["Ngày"].apply(parse_any_date)
            sub = cong_df[cong_df["Ngày"].dt.date == pd.to_datetime(ngay_cong).date()]
            if not sub.empty:
                # đưa về dạng 2 nửa ngày
                def split_row(r):
                    if r.get("Ca") == "Full ngày": return (1,1)
                    if r.get("Ca") == "Nửa ngày sáng": return (1,0)
                    if r.get("Ca") == "Nửa ngày chiều": return (0,1)
                    return (0,0)
                tmp = []
                for _, r in sub.iterrows():
                    s, c = split_row(r)
                    tmp.append({"Nhân viên": r.get("Nhân viên",""), "Sáng": bool(s), "Chiều": bool(c), "Ghi chú": r.get("Ghi chú","")})
                existed = pd.DataFrame(tmp)

        base = pd.DataFrame({"Nhân viên": nhanvien_list})
        base = base.merge(existed, on="Nhân viên", how="left")
        base["Sáng"] = base["Sáng"].fillna(False)
        base["Chiều"] = base["Chiều"].fillna(False)
        base["Ghi chú"] = base["Ghi chú"].fillna("")

        edited = st.data_editor(
            base,
            key="cong_editor",
            use_container_width=True,
            column_config={
                "Nhân viên": st.column_config.TextColumn(disabled=True),
                "Sáng": st.column_config.CheckboxColumn(),
                "Chiều": st.column_config.CheckboxColumn(),
                "Ghi chú": st.column_config.TextColumn(),
            }
        )

        if st.button("Lưu công (ghi đè ngày chọn)", key="cong_save_tbl"):
            rows = []
            for _, r in edited.iterrows():
                sang = bool(r.get("Sáng", False))
                chieu = bool(r.get("Chiều", False))
                if not sang and not chieu:
                    continue
                if sang and chieu:
                    ca = "Full ngày"; cong = 1.0
                elif sang:
                    ca = "Nửa ngày sáng"; cong = 0.5
                else:
                    ca = "Nửa ngày chiều"; cong = 0.5
                rows.append({
                    "Ngày": fmt_date(ngay_cong),
                    "Nhân viên": r["Nhân viên"],
                    "Ca": ca,
                    "Công": cong,
                    "Ghi chú": r.get("Ghi chú","")
                })
            new = pd.DataFrame(rows, columns=["Ngày","Nhân viên","Ca","Công","Ghi chú"])
            replace_rows_by_date("CONG", "Ngày", fmt_date(ngay_cong), new)
            st.success("Đã lưu công cho ngày " + fmt_date(ngay_cong))

# ============================================================
# TAB 5: Nhập hàng (bảng nhập theo sản phẩm)
# ============================================================
with tab5:
    st.subheader("Nhập hàng theo bảng")
    ngay_nhap = st.date_input("Ngày nhập (dd-mm-yyyy)", pd.Timestamp.today(), key="nhap_ngay_tbl")

    items = sorted(set(safe_inventory_items() + safe_options("Mặt hàng")))
    if not items:
        st.info("Chưa có danh sách Mặt hàng trong LOOKUPS/INVENTORY.")
    else:
        nhap = read_df("NHAP_HANG")
        existed = pd.DataFrame(columns=["Mặt hàng","Số lượng nhập","Đơn giá","Nhà cung cấp","Ghi chú"])
        if not nhap.empty:
            nhap["Ngày"] = nhap["Ngày"].apply(parse_any_date)
            sub = nhap[nhap["Ngày"].dt.date == pd.to_datetime(ngay_nhap).date()]
            if not sub.empty:
                existed = sub[["Mặt hàng","Số lượng nhập","Đơn giá","Nhà cung cấp","Ghi chú"]].copy()

        base = pd.DataFrame({"Mặt hàng": items})
        base = base.merge(existed, on="Mặt hàng", how="left")
        base["Số lượng nhập"] = pd.to_numeric(base["Số lượng nhập"], errors="coerce").fillna(0).astype(int)
        base["Đơn giá"] = pd.to_numeric(base["Đơn giá"], errors="coerce").fillna(0).astype(int)
        base["Nhà cung cấp"] = base["Nhà cung cấp"].fillna("")
        base["Ghi chú"] = base["Ghi chú"].fillna("")

        edited = st.data_editor(
            base,
            key="nhap_editor",
            use_container_width=True,
            column_config={
                "Mặt hàng": st.column_config.TextColumn(disabled=True),
                "Số lượng nhập": st.column_config.NumberColumn(min_value=0, step=1),
                "Đơn giá": st.column_config.NumberColumn(min_value=0, step=1),
                "Nhà cung cấp": st.column_config.TextColumn(),
                "Ghi chú": st.column_config.TextColumn(),
            }
        )

        if st.button("Lưu nhập hàng (ghi đè ngày chọn)", key="nhap_save_tbl"):
            out = edited.copy()
            out.insert(0, "Ngày", fmt_date(ngay_nhap))
            replace_rows_by_date("NHAP_HANG", "Ngày", fmt_date(ngay_nhap),
                                 out[["Ngày","Mặt hàng","Số lượng nhập","Đơn giá","Nhà cung cấp","Ghi chú"]])
            st.success("Đã lưu nhập hàng cho ngày " + fmt_date(ngay_nhap))
