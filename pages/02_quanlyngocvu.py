# pages/02_quanlyngocvu.py
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from utils.gs import read_df, write_df, options, add_lookup, replace_rows_by_date

DATE_FMT_SAVE = "%d-%m-%Y"

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

def safe_options(kind):
    try:
        vals = options(kind) or []
        vals = [v for v in vals if str(v).strip()]
        return sorted(set(vals))
    except Exception:
        return []

st.set_page_config(page_title="quanlyngocvu", layout="wide")
st.title("Quản lý Ngọc Vũ")

tab1, tab2, tab3 = st.tabs(
    ["Thống kê doanh thu", "Đối chiếu tồn kho", "Lương & Hoa hồng"]
)

# =======================
# TAB 1: Thống kê doanh thu (full filter)
# =======================
with tab1:
    st.subheader("Báo cáo theo ngày với bộ lọc đầy đủ")

    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        src = st.multiselect("Nguồn", ["XE_MAY","OTO"], default=["XE_MAY","OTO"], key="ql_stat_src")
    with c2:
        dfrom = st.date_input("Từ ngày", pd.Timestamp.today().replace(day=1), key="ql_stat_from")
    with c3:
        dto = st.date_input("Đến ngày", pd.Timestamp.today(), key="ql_stat_to")

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
        df = df[(df["Ngày"] >= pd.to_datetime(dfrom)) & (df["Ngày"] <= pd.to_datetime(dto))]

        df["Khách"] = df.get("Khách hàng/Địa chỉ", df.get("Khách hàng", ""))
        df["Loại sản phẩm"] = df.get("Loại sản phẩm", "")
        df["PP Thanh toán"] = df.get("PP Thanh toán", "")

        f1, f2, f3 = st.columns(3)
        with f1:
            kh = st.multiselect("Khách hàng", sorted(df["Khách"].dropna().astype(str).unique().tolist()), key="ql_stat_kh")
        with f2:
            lsp = st.multiselect("Loại sản phẩm", sorted(df["Loại sản phẩm"].dropna().astype(str).unique().tolist()), key="ql_stat_lsp")
        with f3:
            pp = st.multiselect("PP Thanh toán", sorted(df["PP Thanh toán"].dropna().astype(str).unique().tolist()), key="ql_stat_pp")

        if kh: df = df[df["Khách"].astype(str).isin(kh)]
        if lsp: df = df[df["Loại sản phẩm"].astype(str).isin(lsp)]
        if pp: df = df[df["PP Thanh toán"].astype(str).isin(pp)]

        # KPI
        df["SL_Giao"] = 0.0
        df["Vo_ve"] = 0.0

        mask_xm = df["Nguồn"] == "XE_MAY"
        df.loc[mask_xm, "SL_Giao"] = pd.to_numeric(df.loc[mask_xm, "Số lượng giao"], errors="coerce").fillna(0)
        df.loc[mask_xm, "Vo_di"] = df.loc[mask_xm, "SL_Giao"]
        df.loc[mask_xm, "Vo_ve"] = pd.to_numeric(df.loc[mask_xm, "Vỏ về"], errors="coerce").fillna(0)

        mask_oto = df["Nguồn"] == "OTO"
        df.loc[mask_oto, "SL_Giao"] = pd.to_numeric(df.loc[mask_oto, "Số lượng"], errors="coerce").fillna(0)
        df.loc[mask_oto, ["Vo_di","Vo_ve"]] = 0

        grp = df.groupby(df["Ngày"].dt.date).agg(
            SL_Giao=("SL_Giao","sum"),
            Vo_di=("Vo_di","sum"),
            Vo_ve=("Vo_ve","sum"),
        ).reset_index().rename(columns={"Ngày":"Mốc"})
        grp["Mốc"] = pd.to_datetime(grp["Mốc"]).dt.strftime(DATE_FMT_SAVE)
        st.dataframe(grp, use_container_width=True)
        st.bar_chart(grp.set_index("Mốc")["SL_Giao"])

# =======================
# TAB 2: Đối chiếu tồn kho theo ngày
# =======================
with tab2:
    st.subheader("Đối chiếu tồn kho theo ngày")
    ngay_dc = st.date_input("Ngày đối chiếu (dd-mm-yyyy)", pd.Timestamp.today(), key="dc_ngay")
    ngay_truoc = pd.to_datetime(ngay_dc) - timedelta(days=1)

    # Lấy danh sách sản phẩm từ LOOKUPS
    items = safe_options("Mặt hàng")

    # DAILY_CLOSE (tồn cuối)
    close = read_df("DAILY_CLOSE")
    if not close.empty:
        close["Ngày"] = close["Ngày"].apply(parse_any_date)
    else:
        close = pd.DataFrame(columns=["Ngày","Mặt hàng","Tồn cuối"])

    ton_prev = close[close["Ngày"].dt.date == ngay_truoc.date()].groupby("Mặt hàng")["Tồn cuối"].sum()
    ton_curr = close[close["Ngày"].dt.date == pd.to_datetime(ngay_dc).date()].groupby("Mặt hàng")["Tồn cuối"].sum()

    # NHẬP_HÀNG trong ngày
    nhap = read_df("NHAP_HANG")
    if not nhap.empty:
        nhap["Ngày"] = nhap["Ngày"].apply(parse_any_date)
        k = nhap[nhap["Ngày"].dt.date == pd.to_datetime(ngay_dc).date()].groupby("Mặt hàng")["Số lượng nhập"].sum()
    else:
        k = pd.Series(dtype=float)

    # Xuất thực tế (tính từ đơn hàng) trong ngày
    # XE_MAY: Số lượng giao theo Loại sản phẩm
    xm = read_df("XE_MAY")
    if not xm.empty:
        xm["Ngày"] = xm["Ngày"].apply(parse_any_date)
        xm_day = xm[xm["Ngày"].dt.date == pd.to_datetime(ngay_dc).date()]
        x1 = pd.to_numeric(xm_day.get("Số lượng giao", 0), errors="coerce")
        z1 = x1.groupby(xm_day.get("Loại sản phẩm", "")).sum()
    else:
        z1 = pd.Series(dtype=float)

    # OTO: Số lượng theo Loại sản phẩm
    ot = read_df("OTO")
    if not ot.empty:
        ot["Ngày"] = ot["Ngày"].apply(parse_any_date)
        ot_day = ot[ot["Ngày"].dt.date == pd.to_datetime(ngay_dc).date()]
        x2 = pd.to_numeric(ot_day.get("Số lượng", 0), errors="coerce")
        z2 = x2.groupby(ot_day.get("Loại sản phẩm", "")).sum()
    else:
        z2 = pd.Series(dtype=float)

    z_act = z1.add(z2, fill_value=0)

    # Tổng hợp theo danh mục sản phẩm
    all_items = sorted(set(items) | set(ton_prev.index) | set(ton_curr.index) | set(k.index) | set(z_act.index))
    rows = []
    for it in all_items:
        X = float(ton_prev.get(it, 0) or 0)
        K = float(k.get(it, 0) or 0)
        Y = float(ton_curr.get(it, 0) or 0)
        Zexp = X + K - Y
        Zact = float(z_act.get(it, 0) or 0)
        rows.append({
            "Mặt hàng": it,
            "Tồn hôm qua (X)": int(X),
            "Nhập hôm nay (K)": int(K),
            "Tồn hôm nay (Y)": int(Y),
            "Xuất kỳ vọng (Zexp=X+K-Y)": int(Zexp),
            "Xuất thực tế (Zact)": int(Zact),
            "Chênh lệch (Zexp-Zact)": int(Zexp - Zact),
        })
    out = pd.DataFrame(rows)
    st.dataframe(out, use_container_width=True)

# =======================
# TAB 3: Lương & Hoa hồng (thiết lập + bảng tính)
# =======================
with tab3:
    st.subheader("Thiết lập & tính lương theo tháng")
    thang = st.text_input("Tháng (mm/YYYY)", value=pd.Timestamp.today().strftime("%m/%Y"), key="pay_month2")

    colA, colB = st.columns(2)
    # --- PAY_RULES: lương cơ bản / đơn giá công / phụ cấp ---
    with colA:
        st.markdown("**Thiết lập lương cơ bản** (`PAY_RULES`)")
        pay = read_df("PAY_RULES")
        pay = pay if not pay.empty else pd.DataFrame(columns=["Tháng","Nhân viên","Luong_co_ban","Don_gia_cong","Phu_cap","Tam_ung","Khau_tru"])
        pay_cur = pay[pay.get("Tháng","") == thang].copy()
        if pay_cur.empty:
            # khởi tạo theo danh sách nhân viên (LOOKUPS)
            nv = safe_options("Nhân viên") or safe_options("Người chở")
            pay_cur = pd.DataFrame({"Tháng": [thang]*len(nv), "Nhân viên": nv,
                                    "Luong_co_ban": 0, "Don_gia_cong": 250000, "Phu_cap": 0, "Tam_ung": 0, "Khau_tru": 0})
        pay_edit = st.data_editor(
            pay_cur,
            key="pay_rules_edit",
            use_container_width=True,
            column_config={
                "Tháng": st.column_config.TextColumn(disabled=True),
                "Nhân viên": st.column_config.TextColumn(),
                "Luong_co_ban": st.column_config.NumberColumn(min_value=0, step=1000),
                "Don_gia_cong": st.column_config.NumberColumn(min_value=0, step=1000),
                "Phu_cap": st.column_config.NumberColumn(min_value=0, step=1000),
                "Tam_ung": st.column_config.NumberColumn(min_value=0, step=1000),
                "Khau_tru": st.column_config.NumberColumn(min_value=0, step=1000),
            }
        )
        if st.button("Lưu PAY_RULES (ghi đè tháng)", key="save_pay_rules"):
            # ghi đè theo tháng
            base = pay[pay.get("Tháng","") != thang].copy()
            base = pd.concat([base, pay_edit], ignore_index=True)
            write_df("PAY_RULES", base)
            st.success("Đã lưu PAY_RULES cho tháng " + thang)

    # --- COMMISSION_RULES: hoa hồng theo sản phẩm ---
    with colB:
        st.markdown("**Thiết lập hoa hồng theo sản phẩm** (`COMMISSION_RULES`)")
        com = read_df("COMMISSION_RULES")
        com = com if not com.empty else pd.DataFrame(columns=["Tháng","Mặt hàng","Ty_le_%","Hoa_hong_moi_donvi"])
        items = safe_options("Mặt hàng")
        com_cur = com[com.get("Tháng","") == thang].copy()
        if com_cur.empty:
            com_cur = pd.DataFrame({"Tháng":[thang]*len(items), "Mặt hàng": items, "Ty_le_%": 0.0, "Hoa_hong_moi_donvi": 0})
        com_edit = st.data_editor(
            com_cur,
            key="com_rules_edit",
            use_container_width=True,
            column_config={
                "Tháng": st.column_config.TextColumn(disabled=True),
                "Mặt hàng": st.column_config.TextColumn(),
                "Ty_le_%": st.column_config.NumberColumn(min_value=0.0, step=0.5),
                "Hoa_hong_moi_donvi": st.column_config.NumberColumn(min_value=0, step=100),
            }
        )
        if st.button("Lưu COMMISSION_RULES (ghi đè tháng)", key="save_com_rules"):
            base = com[com.get("Tháng","") != thang].copy()
            base = pd.concat([base, com_edit], ignore_index=True)
            write_df("COMMISSION_RULES", base)
            st.success("Đã lưu COMMISSION_RULES cho tháng " + thang)

    st.markdown("---")
    st.markdown("### Bảng tính lương tháng")

    # Công theo tháng
    cong = read_df("CONG")
    if not cong.empty:
        cong["Ngày"] = cong["Ngày"].apply(parse_any_date)
        cong_m = cong[cong["Ngày"].dt.strftime("%m/%Y") == thang].copy()
        cong_sum = cong_m.groupby("Nhân viên")["Công"].sum().reset_index(name="Công")
    else:
        cong_sum = pd.DataFrame(columns=["Nhân viên","Công"])

    # Doanh thu + Số lượng theo nhân viên & mặt hàng (XE_MAY)
    xm = read_df("XE_MAY")
    if not xm.empty:
        xm["Ngày"] = xm["Ngày"].apply(parse_any_date)
        xm_m = xm[xm["Ngày"].dt.strftime("%m/%Y") == thang].copy()
        xm_m["SL"] = pd.to_numeric(xm_m.get("Số lượng giao", 0), errors="coerce").fillna(0)
        xm_m["TT"] = pd.to_numeric(xm_m.get("Thanh Toán", 0), errors="coerce").fillna(0)
        # gộp theo NV & SP để tính hoa hồng theo sản phẩm (nếu có)
        by_nv_sp = xm_m.groupby(["Người chở","Loại sản phẩm"]).agg(SL=("SL","sum"), DT=("TT","sum")).reset_index()
        by_nv_rev = xm_m.groupby(["Người chở"]).agg(DoanhThu=("TT","sum")).reset_index()
        by_nv_rev.rename(columns={"Người chở":"Nhân viên"}, inplace=True)
    else:
        by_nv_sp = pd.DataFrame(columns=["Người chở","Loại sản phẩm","SL","DT"])
        by_nv_rev = pd.DataFrame(columns=["Nhân viên","DoanhThu"])

    # Gộp nhân viên tổng thể
    df = pd.merge(cong_sum, by_nv_rev, on="Nhân viên", how="outer").fillna(0)

    # Rút rules
    pay = read_df("PAY_RULES")
    pay_m = pay[pay.get("Tháng","") == thang].copy() if not pay.empty else pd.DataFrame()
    com = read_df("COMMISSION_RULES")
    com_m = com[com.get("Tháng","") == thang].copy() if not com.empty else pd.DataFrame()

    # Map base salary
    if not pay_m.empty:
        df = pd.merge(df, pay_m[["Nhân viên","Luong_co_ban","Don_gia_cong","Phu_cap","Tam_ung","Khau_tru"]], on="Nhân viên", how="left")
    else:
        df["Luong_co_ban"] = 0
        df["Don_gia_cong"] = 250000
        df["Phu_cap"] = 0
        df["Tam_ung"] = 0
        df["Khau_tru"] = 0

    # Tính lương cơ bản: ưu tiên Luong_co_ban > 0; nếu 0 thì Công * Don_gia_cong
    df["Luong_co_ban"] = pd.to_numeric(df["Luong_co_ban"], errors="coerce").fillna(0)
    df["Don_gia_cong"] = pd.to_numeric(df["Don_gia_cong"], errors="coerce").fillna(250000)
    df["Phu_cap"] = pd.to_numeric(df["Phu_cap"], errors="coerce").fillna(0)
    df["Tam_ung"] = pd.to_numeric(df["Tam_ung"], errors="coerce").fillna(0)
    df["Khau_tru"] = pd.to_numeric(df["Khau_tru"], errors="coerce").fillna(0)
    df["Công"] = pd.to_numeric(df["Công"], errors="coerce").fillna(0.0)

    base_from_day = (df["Công"] * df["Don_gia_cong"]).round(0)
    df["Luong_co_ban_tinh"] = df["Luong_co_ban"].where(df["Luong_co_ban"] > 0, base_from_day)

    # Tính hoa hồng:
    # - Nếu có COMMISSION_RULES theo sản phẩm:
    #     + Nếu "Hoa_hong_moi_donvi" > 0 => SL * đơn vị
    #     + Else nếu "Ty_le_%" > 0 => áp % trên DoanhThu NV (fallback)
    # - Nếu không có rule => fallback 2% DoanhThu
    hoa_hong_nv = {}
    if not by_nv_sp.empty and not com_m.empty:
        # build map sp -> (rate%, per_unit)
        com_m["Ty_le_%"] = pd.to_numeric(com_m["Ty_le_%"], errors="coerce").fillna(0.0)
        com_m["Hoa_hong_moi_donvi"] = pd.to_numeric(com_m["Hoa_hong_moi_donvi"], errors="coerce").fillna(0)
        rate_map = {r["Mặt hàng"]: (float(r["Ty_le_%"]), int(r["Hoa_hong_moi_donvi"])) for _, r in com_m.iterrows()}

        for nv in by_nv_sp["Người chở"].unique():
            sub = by_nv_sp[by_nv_sp["Người chở"] == nv]
            total = 0.0
            for _, r in sub.iterrows():
                sp = r["Loại sản phẩm"]
                SL = float(r["SL"] or 0)
                DT = float(r["DT"] or 0)
                rate, per_unit = rate_map.get(sp, (0.0, 0))
                if per_unit and per_unit > 0:
                    total += SL * per_unit
                elif rate and rate > 0:
                    total += DT * rate / 100.0
            if total == 0:
                # fallback 2% doanh thu NV nếu không khớp rule
                dt_nv = float(by_nv_rev.loc[by_nv_rev["Nhân viên"] == nv, "DoanhThu"].sum() or 0)
                total = dt_nv * 0.02
            hoa_hong_nv[nv] = round(total, 0)
    else:
        # Fallback 2% doanh thu
        for _, r in by_nv_rev.iterrows():
            hoa_hong_nv[r["Nhân viên"]] = round(float(r["DoanhThu"] or 0) * 0.02, 0)

    df["Hoa_hồng"] = df["Nhân viên"].map(hoa_hong_nv).fillna(0)

    df["Tổng lương"] = (df["Luong_co_ban_tinh"] + df["Phu_cap"] + df["Hoa_hồng"] - df["Tam_ung"] - df["Khau_tru"]).round(0)
    df.insert(0, "Tháng", thang)

    # Hiển thị đẹp
    for col in ["Luong_co_ban_tinh","Phu_cap","Hoa_hồng","Tam_ung","Khau_tru","Tổng lương"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    st.dataframe(df[["Tháng","Nhân viên","Công","Luong_co_ban_tinh","Phu_cap","Hoa_hồng","Tam_ung","Khau_tru","Tổng lương"]], use_container_width=True)

    if st.button("Ghi vào LUONG (ghi đè tháng)", key="luong_write"):
        old = read_df("LUONG")
        old = old if not old.empty else pd.DataFrame(columns=["Tháng","Nhân viên","Công","Lương cơ bản","Phụ cấp","Hoa hồng","Tạm ứng","Khấu trừ","Tổng lương"])
        # Chuẩn cột theo file đích
        out = df.copy()
        out.rename(columns={
            "Luong_co_ban_tinh":"Lương cơ bản",
            "Phu_cap":"Phụ cấp",
            "Hoa_hồng":"Hoa hồng",
            "Tam_ung":"Tạm ứng",
            "Khau_tru":"Khấu trừ"
        }, inplace=True)
        base = old[old.get("Tháng","") != thang].copy()
        base = pd.concat([base, out[["Tháng","Nhân viên","Công","Lương cơ bản","Phụ cấp","Hoa hồng","Tạm ứng","Khấu trừ","Tổng lương"]]], ignore_index=True)
        write_df("LUONG", base)
        st.success("Đã cập nhật LUONG cho tháng " + thang)
