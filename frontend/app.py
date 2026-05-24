import streamlit as st
import pandas as pd
import requests
import os
import json
from streamlit_option_menu import option_menu
import base64

st.set_page_config(page_title="Kurumsal Doküman Yönetimi", page_icon="⚙️", layout="wide")

st.markdown("""
<style>
    /* Enterprise Theme Overrides */
    .block-container { padding-top: 1rem; padding-bottom: 2rem; }
    .status-badge { padding: 4px 10px; border-radius: 12px; font-size: 0.85em; font-weight: bold; }
    .status-onaylandi { background-color: #e6f4ea; color: #137333; }
    .status-taslak { background-color: #f1f3f4; color: #5f6368; }
    .status-incelemede { background-color: #e8f0fe; color: #1a73e8; }
    .status-reddedildi { background-color: #fce8e6; color: #c5221f; }
    .status-arsivlendi { background-color: #f1f3f4; color: #5f6368; text-decoration: line-through; }
    hr { margin-top: 1em; margin-bottom: 1em; }
</style>
""", unsafe_allow_html=True)

API_URL = os.getenv("API_URL", "http://backend:8000")
PUBLIC_API_URL = "http://localhost:8001"

# --- INITIALIZATION ---
@st.cache_data(ttl=60)
def fetch_users():
    try:
        res = requests.get(f"{API_URL}/users/")
        return res.json() if res.status_code == 200 else []
    except:
        return []

users = fetch_users()
if not users:
    try:
        requests.post(f"{API_URL}/setup")
        users = fetch_users()
    except:
        pass

if 'current_user' not in st.session_state:
    st.session_state.current_user = None

# --- LOGIN SCREEN ---
if st.session_state.current_user is None:
    st.markdown("<h2 style='text-align: center; color: #4CAF50;'>Doküman Yönetimi Sistemine Hoş Geldiniz</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Lütfen sicil numaranız (ID) ve şifrenizle giriş yapınız. (Test şifresi: 123456)</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Sicil No / ID (Örn: 1001, 3001)", placeholder="Sicil No")
            password = st.text_input("Şifre", type="password", placeholder="Şifre")
            submitted = st.form_submit_button("Giriş Yap", use_container_width=True)
            
            if submitted:
                if not username or not password:
                    st.error("Lütfen kullanıcı adı ve şifre giriniz.")
                else:
                    try:
                        res = requests.post(f"{API_URL}/login", data={"username": username.strip().lower(), "password": password})
                        if res.status_code == 200:
                            st.session_state.current_user = res.json()
                            st.rerun()
                        else:
                            st.error("Hatalı kullanıcı adı veya şifre!")
                    except Exception as e:
                        st.error("API'ye ulaşılamadı. Lütfen backend'in çalıştığından emin olun.")
    
    st.stop()  # Stop execution here if not logged in

current_user = st.session_state.current_user

# --- GLOBAL DATA & NOTIFICATIONS ---
try:
    all_docs = requests.get(f"{API_URL}/documents/").json()
except:
    all_docs = []

pending_for_me = []
rejected_for_me = []

for d in all_docs:
    if not d.get('revisions'): continue
    latest_rev = max(d['revisions'], key=lambda x: x['rev_no'])
    
    if latest_rev['status'] == 'İncelemede':
        for app in latest_rev['approvals']:
            if app['user']['id'] == current_user['id'] and app['status'] == 'Bekliyor':
                pending_for_me.append(d)
                break
                
    if latest_rev['status'] == 'Reddedildi' and latest_rev['uploader']['id'] == current_user['id']:
        rejected_for_me.append(d)

if not st.session_state.get('notified_this_session'):
    if pending_for_me:
        st.toast(f"🔔 Onayınızı bekleyen {len(pending_for_me)} doküman var!", icon="⏳")
    if rejected_for_me:
        st.toast(f"⚠️ Yüklediğiniz {len(rejected_for_me)} doküman reddedildi!", icon="❌")
    st.session_state.notified_this_session = True


# --- SIDEBAR & AUTH ---
with st.sidebar:
    st.markdown("""
        <style>
            [data-testid="stSidebarNav"] { display: none; }
            [data-testid="stSidebar"] {
                background-color: #f8fafc;
                border-right: 1px solid #e2e8f0;
            }
            [data-testid="stSidebar"] .block-container {
                padding-top: 1rem !important;
            }
            .sidebar-title {
                font-size: 1.3rem;
                font-weight: 800;
                color: #0f172a;
                margin-top: -10px;
                margin-bottom: 20px;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .user-card {
                background: white;
                padding: 12px;
                border-radius: 10px;
                box-shadow: 0 1px 2px rgba(0,0,0,0.05);
                margin-bottom: 15px;
                border: 1px solid #e2e8f0;
            }
            .user-name { font-weight: 600; color: #1e293b; font-size: 14px; }
            .user-role { color: #64748b; font-size: 12px; margin-top: 2px; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='sidebar-title'>🚀 Kıvılcım DMS</div>", unsafe_allow_html=True)
    st.markdown(f"""
        <div class='user-card'>
            <div class='user-name'>👤 {current_user['name']}</div>
            <div class='user-role'>{current_user['role']}</div>
        </div>
    """, unsafe_allow_html=True)
    
    try:
        notifs = requests.get(f"{API_URL}/notifications/{current_user['id']}").json()
        unread_notifs = [n for n in notifs if not n['is_read']]
    except:
        notifs = []
        unread_notifs = []
        
    if unread_notifs and not st.session_state.get('notif_toasted'):
        st.toast(f"🔔 {len(unread_notifs)} yeni bildiriminiz var!")
        st.session_state.notif_toasted = True
    
    notif_title = f"Bildirimler ({len(unread_notifs)})" if unread_notifs else "Bildirimler"
    
    selected_menu = option_menu(
        "Menü",
        ["Doküman Listesi", "İşlemlerim (Onay/Ret)", "Yeni Doküman / Revizyon", notif_title, "Denetim İzleri", "Çalışan Personeller"],
        icons=['folder2-open', 'check2-all', 'cloud-arrow-up', 'bell-fill' if unread_notifs else 'bell', 'shield-check', 'people-fill'],
        menu_icon="list", default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent", "border": "none"},
            "icon": {"color": "#6366f1", "font-size": "16px"}, 
            "nav-link": {"font-size": "14px", "text-align": "left", "margin":"4px 0", "padding": "10px 15px", "border-radius": "8px", "color": "#334155", "font-family": "sans-serif"},
            "nav-link-selected": {"background-color": "#e0e7ff", "color": "#4338ca", "font-weight": "600"}
        }
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪 Çıkış Yap", use_container_width=True):
        st.session_state.current_user = None
        st.rerun()

def status_html(status_text):
    cls = status_text.lower().replace(" ", "").replace("ı", "i")
    if cls == "bekliyor": cls = "incelemede"
    return f'<span class="status-badge status-{cls}">{status_text}</span>'

# --- ROUTING ---
if 'last_menu' not in st.session_state:
    st.session_state.last_menu = selected_menu

if st.session_state.last_menu != selected_menu:
    st.session_state.view_doc_id = None
    st.session_state.last_menu = selected_menu

if 'view_doc_id' in st.session_state and st.session_state.view_doc_id:
    # DETAY SAYFASI
    doc_id = st.session_state.view_doc_id
    if st.button("← Listeye Dön"):
        st.session_state.view_doc_id = None
        st.rerun()
        
    try:
        doc = requests.get(f"{API_URL}/documents/{doc_id}").json()
        
        c_head1, c_head2 = st.columns([8, 2])
        with c_head1:
            st.header(f"{doc['doc_no']} - {doc['doc_name']}")
            st.markdown(f"**Departman(lar):** {doc.get('department', 'Belirtilmemiş')} | **Kategori:** {doc['category']} | **Oluşturulma:** {doc['created_at'][:10]}")
        with c_head2:
            if current_user['role'] in ["Sistem Yöneticisi", "Kalite Müdürü", "Üretim Müdürü"]:
                del_key = f"confirm_del_{doc_id}"
                if st.session_state.get(del_key):
                    st.error("⚠️ Kalıcı olarak silinecek. Emin misiniz?")
                    col_y, col_n = st.columns(2)
                    if col_y.button("Evet", type="primary", key="btn_yes_del"):
                        requests.delete(f"{API_URL}/documents/{doc_id}")
                        st.session_state.view_doc_id = None
                        st.session_state[del_key] = False
                        st.rerun()
                    if col_n.button("İptal", key="btn_no_del"):
                        st.session_state[del_key] = False
                        st.rerun()
                else:
                    if st.button("🗑️ Dokümanı Sil", type="secondary", use_container_width=True):
                        st.session_state[del_key] = True
                        st.rerun()
        
        revisions = sorted(doc['revisions'], key=lambda x: x['rev_no'], reverse=True)
        if not revisions:
            st.warning("Bu dokümanın hiç revizyonu yok.")
        else:
            tabs = st.tabs([f"Revizyon {r['rev_no']} {'(Onaylandı)' if r['status']=='Onaylandı' else ''}" for r in revisions])
            
            for idx, r in enumerate(revisions):
                with tabs[idx]:
                    colA, colB = st.columns([2, 1])
                    
                    with colA:
                        st.markdown(f"### Revizyon Detayları")
                        st.markdown(f"**Yükleyen:** {r['uploader']['name']} ({r['uploader']['role']})")
                        st.markdown(f"**Durum:** {status_html(r['status'])}", unsafe_allow_html=True)
                        if r['rev_no'] > 0:
                            st.info(f"**Gerekçe:** {r['rev_reason'] or '-'}")
                            st.warning(f"**Etkilenen Operasyon:** {r['affected_op'] or '-'}")
                        
                        st.markdown("---")
                        st.markdown("#### Doküman Önizleme")
                        if r['file_path']:
                            file_url = f"{PUBLIC_API_URL}/files/{r['file_path']}"
                            st.markdown(f'<iframe src="{file_url}" width="100%" height="600px" style="border: 1px solid #ccc; border-radius: 8px;"></iframe>', unsafe_allow_html=True)
                            st.markdown(f"[📥 Dosyayı İndir]({file_url})")
                        else:
                            st.error("PDF bulunamadı.")
                            
                        st.markdown("---")
                        st.markdown("#### 💬 Yorumlar (Sohbet)")
                        
                        chat_container = st.container()
                        with chat_container:
                            for c in r['comments']:
                                is_me = (c['user']['id'] == current_user['id'])
                                with st.chat_message("user" if is_me else "assistant"):
                                    st.markdown(f"**{c['user']['name']}** <span style='font-size:0.8em; color:gray'>({c['created_at'][:16]})</span><br>{c['text']}", unsafe_allow_html=True)
                        
                        with st.form(f"comment_form_{r['id']}", clear_on_submit=True):
                            c1, c2 = st.columns([5, 1])
                            c_text = c1.text_input("Yorum", label_visibility="collapsed", placeholder="Yorumunuzu yazın...")
                            if c2.form_submit_button("Gönder", use_container_width=True):
                                if c_text:
                                    requests.post(f"{API_URL}/revisions/{r['id']}/comments", data={"user_id": current_user['id'], "text": c_text})
                                    st.rerun()
                    
                    with colB:
                        st.markdown("### Onay Akışı")
                        can_approve = False
                        my_approval_id = None
                        
                        for app in r['approvals']:
                            st.markdown(f"👤 **{app['user']['name']}** ({app['user']['role']})")
                            st.markdown(f"Durum: {status_html(app['status'])}", unsafe_allow_html=True)
                            if app['feedback']:
                                st.markdown(f"↳ *Not: {app['feedback']}*")
                            st.markdown("<hr style='margin: 10px 0'>", unsafe_allow_html=True)
                            
                            if app['user']['id'] == current_user['id'] and app['status'] == "Bekliyor" and r['status'] == "İncelemede":
                                can_approve = True
                                my_approval_id = app['id']
                        
                        if can_approve:
                            st.markdown("#### Eylemleriniz")
                            if st.button("✅ Onayla", key=f"app_btn_{r['id']}", use_container_width=True):
                                requests.post(f"{API_URL}/approvals/{my_approval_id}/approve", params={"user_id": current_user['id']})
                                st.rerun()
                                
                            with st.expander("❌ Reddet"):
                                rej_reason = st.text_area("Ret Gerekçesi", key=f"rej_text_{r['id']}")
                                if st.button("Reddet", key=f"rej_btn_{r['id']}"):
                                    if not rej_reason:
                                        st.error("Ret gerekçesi girmelisiniz.")
                                    else:
                                        requests.post(f"{API_URL}/approvals/{my_approval_id}/reject", data={"user_id": current_user['id'], "feedback": rej_reason})
                                        st.rerun()
        
        st.markdown("---")
        with st.expander("➕ Dokümanı Başka Birimlere Dahil Et / Çıkar"):
            all_deps = ["Üretim", "Kalite", "Ar-Ge", "Tasarım", "Bakım"]
            current_deps = [d.strip() for d in doc.get('department', '').split(',')] if doc.get('department') else []
            new_deps = st.multiselect("Birimleri Seçin", all_deps, default=[d for d in current_deps if d in all_deps])
            if st.button("Departmanları Güncelle"):
                requests.put(f"{API_URL}/documents/{doc_id}/departments", data={"departments": ", ".join(new_deps)})
                st.success("Güncellendi!")
                st.rerun()
                
    except Exception as e:
        st.error(f"Hata: {e}")
        
elif selected_menu == "Doküman Listesi":
    # LİSTELEME
    st.header("🗂️ Tüm Dokümanlar")
        
    c1, c2, c3, c4 = st.columns(4)
    search_q = c1.text_input("🔍 Doküman Ara (No, İsim)")
    cat_filter = c2.selectbox("Kategori Filtresi", ["Tümü", "Teknik Resim", "Mastar", "Kalıp", "Operasyon Planı", "Talimat", "Prosedür"])
    dep_filter = c3.selectbox("Departman Filtresi", ["Tümü", "Üretim", "Kalite", "Ar-Ge", "Tasarım", "Bakım"])
    durum_filter = c4.selectbox("Durum", ["Güncel", "Arşiv"])

    flat_revisions = []
    for d in all_docs:
        if cat_filter != "Tümü" and d['category'] != cat_filter: continue
        if dep_filter != "Tümü":
            doc_deps = [dep.strip() for dep in d.get('department', '').split(',')]
            if dep_filter not in doc_deps: continue
        if search_q and search_q.lower() not in d['doc_no'].lower() and search_q.lower() not in d['doc_name'].lower(): continue
        
        if not d.get('revisions'): continue
        
        max_rev = max(r['rev_no'] for r in d['revisions'])
        
        for r in d['revisions']:
            is_latest = (r['rev_no'] == max_rev)
            
            if is_latest and r['status'] != "Reddedildi":
                is_archive = False
                archive_reason = ""
            elif is_latest and r['status'] == "Reddedildi":
                is_archive = True
                archive_reason = "Reddedildi"
            else:
                is_archive = True
                archive_reason = "Revize Edildi"
                
            if durum_filter == "Güncel" and not is_archive:
                flat_revisions.append({"doc": d, "rev": r, "archive_reason": archive_reason})
            elif durum_filter == "Arşiv" and is_archive:
                flat_revisions.append({"doc": d, "rev": r, "archive_reason": archive_reason})
            
    if not flat_revisions:
        st.info("Doküman bulunamadı.")
    else:
        st.markdown("<hr style='margin: 0.5em 0; border: 0; border-top: 2px solid #ddd;'>", unsafe_allow_html=True)
        for item in flat_revisions:
            d = item['doc']
            r = item['rev']
            status = status_html(r['status'])
            rev_no = r['rev_no']
            
            c_info, c_btn = st.columns([6, 1])
            with c_info:
                reason_html = f"<span style='float:right; color:#ef4444; font-weight:bold; font-size:13px;'>({item['archive_reason']})</span>" if item['archive_reason'] else ""
                st.markdown(f"**{d['doc_no']} - {d['doc_name']}** &nbsp;&nbsp; {status} {reason_html} <br> <span style='font-size:0.85em; color:gray;'>Departman: {d.get('department', '-')} | Kategori: {d['category']} | Revizyon: {rev_no}</span>", unsafe_allow_html=True)
            with c_btn:
                if st.button("Detaylar", key=f"view_rev_{r['id']}", use_container_width=True):
                    st.session_state.view_doc_id = d['id']
                    st.rerun()
            st.markdown("<hr style='margin: 0.5em 0; border: 0; border-top: 1px solid #eee;'>", unsafe_allow_html=True)

elif selected_menu == "İşlemlerim (Onay/Ret)":
    st.markdown("### ✅ İşlemlerim")
    st.markdown("<p style='font-size:0.9em; color:gray;'>Onayınızı bekleyen veya reddedilen dokümanlarınızı buradan takip edebilirsiniz.</p>", unsafe_allow_html=True)
    
    col_p, col_r = st.columns(2)
    
    with col_p:
        st.markdown("#### ⏳ Onayımı Bekleyenler")
        if not pending_for_me:
            st.info("Şu an onayınızı bekleyen bir belge bulunmuyor.")
        else:
            st.markdown("<hr style='margin: 0.5em 0; border: 0; border-top: 2px solid #ddd;'>", unsafe_allow_html=True)
            for d in pending_for_me:
                latest_rev = max(d['revisions'], key=lambda x: x['rev_no'])
                c_info, c_btn = st.columns([4, 1.2])
                with c_info:
                    st.markdown(f"**<span style='color:#1a73e8;'>{d['doc_no']}</span> - {d['doc_name']}** <br> <span style='font-size:0.85em; color:gray;'>Revizyon: {latest_rev['rev_no']} | {d['category']}</span>", unsafe_allow_html=True)
                with c_btn:
                    if st.button("İncele", key=f"action_pend_{d['id']}", type="primary", use_container_width=True):
                        st.session_state.view_doc_id = d['id']
                        st.warning("Detay için sol menüden 'Doküman Listesi'ni seçin.")
                st.markdown("<hr style='margin: 0.5em 0; border: 0; border-top: 1px solid #eee;'>", unsafe_allow_html=True)

    with col_r:
        st.markdown("#### ❌ Reddedilen Dokümanlarım")
        if not rejected_for_me:
            st.info("Reddedilen bir dokümanınız bulunmuyor.")
        else:
            st.markdown("<hr style='margin: 0.5em 0; border: 0; border-top: 2px solid #ddd;'>", unsafe_allow_html=True)
            for d in rejected_for_me:
                latest_rev = max(d['revisions'], key=lambda x: x['rev_no'])
                c_info, c_btn = st.columns([4, 1.2])
                with c_info:
                    st.markdown(f"**<span style='color:#c5221f;'>{d['doc_no']}</span> - {d['doc_name']}** <br> <span style='font-size:0.85em; color:gray;'>Revizyon: {latest_rev['rev_no']} | {d['category']}</span>", unsafe_allow_html=True)
                with c_btn:
                    if st.button("Düzelt", key=f"action_rej_{d['id']}", use_container_width=True):
                        st.session_state.view_doc_id = d['id']
                        st.warning("Detay için sol menüden 'Doküman Listesi'ni seçin.")
                st.markdown("<hr style='margin: 0.5em 0; border: 0; border-top: 1px solid #eee;'>", unsafe_allow_html=True)

elif selected_menu == "Yeni Doküman / Revizyon":
    st.header("📤 Doküman Yükleme Merkezi")
    if current_user and current_user['role'] in ["Operatör"]:
        st.warning("Yetki Hatası: Sadece mühendisler veya yöneticiler doküman yükleyebilir.")
    else:
        upload_type = st.radio("İşlem Tipi", ["Yeni Doküman Yükle", "Mevcut Dokümana Revizyon Ekle"], horizontal=True)
        
        with st.form("upload_form"):
            if upload_type == "Yeni Doküman Yükle":
                col1, col2 = st.columns(2)
                doc_no = col1.text_input("Doküman No (Örn: TR-001)")
                doc_name = col2.text_input("Doküman Adı")
                
                col3, col4 = st.columns(2)
                category = col3.selectbox("Kategori", ["Teknik Resim", "Mastar", "Kalıp", "Operasyon Planı", "Montaj Talimatı", "Kalite Belgesi", "Prosedür"])
                department = col4.multiselect("Departman(lar)", ["Üretim", "Kalite", "Ar-Ge", "Tasarım", "Bakım"])
                
                rev_reason = ""
                affected_op = ""
            else:
                try:
                    all_docs = requests.get(f"{API_URL}/documents/").json()
                except:
                    all_docs = []
                
                default_appr_ids = []
                doc_options = {d['id']: f"{d['doc_no']} - {d['doc_name']}" for d in all_docs}
                if not doc_options:
                    st.warning("Sistemde henüz doküman bulunmuyor. Lütfen 'Yeni Doküman Yükle' seçeneğini kullanın.")
                    selected_doc_id = None
                    doc_no, doc_name, category, department = "", "", "", ""
                else:
                    selected_doc_id = st.selectbox("Doküman Seç", options=list(doc_options.keys()), format_func=lambda x: doc_options[x])
                    selected_doc = next(d for d in all_docs if d['id'] == selected_doc_id)
                    doc_no = selected_doc['doc_no']
                    doc_name = selected_doc['doc_name']
                    category = selected_doc['category']
                    department = [] # Revizyon için departman doc üzerinden gelir.
                    
                    # Compute defaults for approvers
                    for rev in selected_doc.get('revisions', []):
                        if rev['uploader']['id'] not in default_appr_ids:
                            default_appr_ids.append(rev['uploader']['id'])
                        for app in rev.get('approvals', []):
                            if app['user']['id'] not in default_appr_ids:
                                default_appr_ids.append(app['user']['id'])
                    
                rev_reason = st.text_area("Revizyon Gerekçesi (Zorunlu)")
                affected_op = st.text_input("Etkilenen Operasyonlar")
            
            st.markdown("### Onay Akışı")
            st.info("Lütfen bu dokümanı onaylayacak yöneticileri seçin. (Kalite ve Üretim yöneticilerinin onayı genellikle zorunludur.)")
            approver_users = [u for u in users if u['role'] in ["Kalite Müdürü", "Üretim Müdürü", "Mühendis / Kontrolör", "Sistem Yöneticisi"]]
            
            valid_defaults = [uid for uid in default_appr_ids if any(u['id'] == uid for u in approver_users)] if upload_type == "Mevcut Dokümana Revizyon Ekle" else []
            
            if valid_defaults:
                st.markdown("**📌 Zorunlu Önceki Onaycılar (Otomatik Eklendi):**")
                for def_id in valid_defaults:
                    def_user = next((u for u in users if u['id'] == def_id), None)
                    if def_user:
                        st.markdown(f"- {def_user['name']} ({def_user['role']})")
            
            available_for_select = [u['id'] for u in approver_users if u['id'] not in valid_defaults]
            
            selected_extra = st.multiselect(
                "Ek Onaycılar (İsteğe Bağlı)" if valid_defaults else "Onaycılar", 
                options=available_for_select,
                format_func=lambda x: next(u['name'] + f" ({u['role']})" for u in users if u['id'] == x)
            )
            
            final_approvers = valid_defaults + selected_extra
            
            st.markdown("### Dosya Detayları")
            uploaded_file = st.file_uploader("PDF Dosyası", type=["pdf"])
            
            submitted = st.form_submit_button("Sisteme Yükle", type="primary")
            if submitted:
                if upload_type == "Mevcut Dokümana Revizyon Ekle" and not selected_doc_id:
                    st.error("Lütfen bir doküman seçin.")
                elif upload_type == "Mevcut Dokümana Revizyon Ekle" and not rev_reason:
                    st.error("Revizyon gerekçesi belirtmek zorunludur.")
                elif not doc_no or not doc_name or not uploaded_file or not final_approvers:
                    st.error("Lütfen tüm zorunlu alanları doldurun (Dosya ve Onaycılar dahil).")
                else:
                    data = {
                        "doc_no": doc_no,
                        "doc_name": doc_name,
                        "category": category,
                        "department": ", ".join(department) if isinstance(department, list) else department,
                        "rev_reason": rev_reason,
                        "affected_op": affected_op,
                        "uploader_id": current_user['id'],
                        "approvals": json.dumps(final_approvers)
                    }
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                    
                    with st.spinner("Yükleniyor..."):
                        res = requests.post(f"{API_URL}/documents/", data=data, files=files)
                        if res.status_code == 200:
                            st.success("Başarıyla yüklendi ve onay akışı başlatıldı!")
                        else:
                            st.error(f"Hata: {res.text}")

elif selected_menu.startswith("Bildirimler"):
    st.header("🔔 Bildirimler")
    if not notifs:
        st.info("Hiç bildiriminiz yok.")
    else:
        try:
            all_docs = requests.get(f"{API_URL}/documents/").json()
        except:
            all_docs = []
            
        # CSS for notification rows
        st.markdown("""
        <style>
        .notif-row {
            padding: 12px 15px;
            border-radius: 8px;
            margin-bottom: 8px;
            border: 1px solid #e2e8f0;
            display: flex;
            align-items: center;
        }
        .notif-unread {
            background-color: #e0f2fe;
            border-left: 4px solid #0284c7;
            font-weight: 600;
        }
        .notif-read {
            background-color: #ffffff;
            border-left: 4px solid #e2e8f0;
            color: #64748b;
        }
        </style>
        """, unsafe_allow_html=True)
        
        for n in notifs:
            target_doc_id = None
            for d in all_docs:
                if d['doc_no'] in n['message']:
                    target_doc_id = d['id']
                    break
            
            c_star, c_msg, c_btn = st.columns([1, 10, 2])
            
            with c_star:
                if st.button("⭐" if n.get('is_starred') else "☆", key=f"star_{n['id']}"):
                    requests.post(f"{API_URL}/notifications/{n['id']}/star")
                    st.rerun()
            
            with c_msg:
                row_class = "notif-unread" if not n['is_read'] else "notif-read"
                st.markdown(f"""
                <div class='notif-row {row_class}'>
                    <div style="flex-grow: 1;">{n['message']}</div>
                    <div style="font-size: 0.8em; color: gray; margin-left: 10px;">{n['created_at'][:16].replace('T', ' ')}</div>
                </div>
                """, unsafe_allow_html=True)
                
            with c_btn:
                if st.button("📂 Aç", key=f"open_{n['id']}", use_container_width=True):
                    if not n['is_read']:
                        requests.post(f"{API_URL}/notifications/{n['id']}/read")
                    if target_doc_id:
                        st.session_state.view_doc_id = target_doc_id
                    st.rerun()

elif selected_menu == "Denetim İzleri":
    st.header("📋 Sistem Denetim Logları")
    st.markdown("Tüm kullanıcı eylemleri ve sistem kayıtları burada listelenir.")
    try:
        logs = requests.get(f"{API_URL}/audit-logs/").json()
        if logs:
            df = pd.DataFrame(logs)
            df = df[['timestamp', 'user_name', 'role', 'action', 'target']]
            df.columns = ["Zaman", "Kullanıcı", "Rol", "İşlem", "Hedef"]
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Kayıt bulunamadı.")
    except:
        st.error("Loglar alınamadı.")

elif selected_menu == "Çalışan Personeller":
    st.header("👥 Çalışan Personel Listesi")
    st.markdown("Sistemde kayıtlı olan tüm yöneticiler ve personeller burada yer almaktadır.")
    try:
        users_data = requests.get(f"{API_URL}/users/").json()
        if users_data:
            df = pd.DataFrame(users_data)
            df = df[['username', 'name', 'role']]
            df.columns = ["Sicil Numarası", "Ad Soyad", "Unvan / Departman"]
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Sistemde kayıtlı personel bulunamadı.")
    except:
        st.error("Personel bilgileri sunucudan alınamadı.")
