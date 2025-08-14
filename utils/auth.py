import streamlit as st
from google.oauth2.service_account import Credentials
import gspread

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

@st.cache_resource(show_spinner=False)
def get_client():
    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=SCOPES
    )
    return gspread.authorize(creds)

@st.cache_resource(show_spinner=False)
def get_spreadsheet():
    client = get_client()
    return client.open_by_key(st.secrets["sheets"]["SPREADSHEET_ID"])
