import streamlit as st

st.set_page_config(page_title="Ngọc Vũ - SX & Bán Nước", layout="wide")
st.title("Hệ thống quản lý sản xuất & bán nước - Ngọc Vũ")

st.markdown(
    "- Vào **Trang Đơn Hàng** để nhập liệu, xem bảng, chốt tồn kho ngày, và điểm danh.\n"
    "- Vào **Trang Quản Lý** để xem báo cáo, đối chiếu tồn kho và tính lương/hoa hồng."
)

st.info("Dùng menu bên trái để chuyển trang. Mỗi trang có link riêng sau khi deploy: 'donhangngocvu' và 'quanlyngocvu'.")
