# app.py
# -*- coding: utf-8 -*-

import os
import io
import math
import datetime as dt
import pandas as pd
import streamlit as st

# =========================
# تنظیمات اولیه
# =========================
st.set_page_config(
    page_title="سیستم ثبت زمان گروه حقوقی گرشا",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# استایل لوکس
# =========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;600;700;800&display=swap');
html, body, [class*="css"]  {
    font-family: 'Vazirmatn', sans-serif;
}
.main-title {
    background: linear-gradient(90deg,#0f172a,#1e3a8a,#0369a1);
    color: white;
    padding: 22px;
    border-radius: 18px;
    text-align: center;
    box-shadow: 0 8px 25px rgba(2,6,23,.25);
    margin-bottom: 14px;
}
.card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 14px;
    box-shadow: 0 4px 12px rgba(15,23,42,.05);
}
.small-note {
    color: #334155;
    font-size: 0.9rem;
}
</style>
""", unsafe_allow_html=True)

# =========================
# مسیر داده‌ها
# =========================
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

CODES_FILE = os.path.join(DATA_DIR, "codes.csv")
TIME_FILE = os.path.join(DATA_DIR, "time_logs.csv")
LEADS_FILE = os.path.join(DATA_DIR, "leads.csv")
PROJECTS_FILE = os.path.join(DATA_DIR, "projects.csv")

# =========================
# ثابت‌ها
# =========================
ACTIVITY_CODES = ["BILL", "NBC", "BD", "PRO", "TRN", "ADM", "INT", "BRK", "OFF"]
BILLABLE_MAP = {
    "BILL": "بله",
    "NBC": "خیر",
    "BD": "خیر",
    "PRO": "خیر",
    "TRN": "خیر",
    "ADM": "خیر",
    "INT": "خیر",
    "BRK": "خیر",
    "OFF": "خیر"
}
PAID_CODES = {"BILL", "NBC", "BD", "PRO", "TRN", "ADM", "INT"}  # BRK/OFF بدون حقوق

APPROVERS = ["دکتر میرشهبیز شافع", "خانم زهرا گرگیج"]

MONTHS_FA = [
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
]


def round_to_0_1(x):
    return round(x * 10) / 10.0


def parse_time_str(t):
    # انتظار HH:MM
    try:
        return dt.datetime.strptime(t, "%H:%M")
    except:
        return None


def ensure_df(file_path, columns):
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        for c in columns:
            if c not in df.columns:
                df[c] = ""
        return df[columns]
    return pd.DataFrame(columns=columns)


# =========================
# ساخت دیتافریم‌ها
# =========================
codes_cols = [
    "کد پرونده یا کد پروژه", "موکل یا عنوان", "کد محصول", "شرح کد محصول",
    "افراد", "دلیل عدم صورت حساب", "تایید کننده"
]
time_cols = [
    "تاریخ (شمسی)", "ماه", "هفته", "ثبت‌کننده", "از ساعت", "تا ساعت", "مدت (ساعت)",
    "کد پرونده / پروژه", "موکل", "کد محصول", "کد فعالیت", "شرح کار",
    "قابل صورت‌حساب؟", "دلیل عدم صورت‌حساب", "تأییدکننده", "بررسی"
]
leads_cols = [
    "تاریخ (شمسی)", "ماه", "ساعت تماس", "نام تماس‌گیرنده", "شماره تماس",
    "منبع / کانال", "کد محصول", "موضوع در یک خط",
    "ساعت یا روز درخواستی برای مشاوره", "نتیجه", "تاریخ ارسال پیشنهاد کتبی"
]
projects_cols = [
    "کد پروژه", "نام پروژه", "حامی (شریک)", "خروجی قابل تحویل",
    "مهلت", "سقف ساعت ماهانه", "ساعت مصرف‌شده (خودکار)", "وضعیت (خودکار)", "ماه و سال"
]

codes_df = ensure_df(CODES_FILE, codes_cols)
time_df = ensure_df(TIME_FILE, time_cols)
leads_df = ensure_df(LEADS_FILE, leads_cols)
projects_df = ensure_df(PROJECTS_FILE, projects_cols)

# =========================
# هدر
# =========================
st.markdown('<div class="main-title"><h2>⚖️ سیستم ثبت زمان گروه حقوقی گرشا</h2><p>نسخه ۱ — جایگزین اکسل روزانه قدیم</p></div>', unsafe_allow_html=True)

# =========================
# تب‌ها
# =========================
tabs = st.tabs(["📘 راهنما", "🧩 کدها", "⏱️ ثبت زمان", "📞 مراجعات", "🗂️ پروژه‌ها", "📊 داشبورد"])

# -------------------------
# TAB 1 - راهنما
# -------------------------
with tabs[0]:
    st.markdown("### گروه حقوقی گرشا — سامانه ثبت زمان و بهره‌وری")
    st.info("از امروز، ثبت روزانه فقط در همین سامانه انجام می‌شود. سطرها فقط اضافه می‌شوند و پاک/بازنویسی نمی‌گردند.")
    st.markdown("""
**پنج قاعده ثبت — بدون استثنا**
1. هم‌زمان بنویس، نه پایان روز  
2. واحد شش‌دقیقه‌ای (۰٫۱ ساعت)  
3. یک کد فعالیت برای هر سطر  
4. آزمون شرح: «آیا موکل این جمله را می‌پردازد؟»  
5. ستون «بررسی» باید «کامل» باشد  

**نه کد فعالیت**
- BILL, NBC, BD, PRO, TRN, ADM, INT, BRK, OFF

**نقش برگه‌ها**
- ثبت زمان: همه
- مراجعات: کارشناس دفتری
- داشبورد: خودکار
- پروژه‌ها: شرکا
- کدها: مدیر دفتر
""")

# -------------------------
# TAB 2 - کدها
# -------------------------
with tabs[1]:
    st.markdown("### تب کدها")
    with st.form("codes_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            code_case_proj = st.text_input("کد پرونده یا کد پروژه")
            product_code = st.text_input("کد محصول")
            persons = st.text_input("افراد")
        with c2:
            client_title = st.text_input("موکل یا عنوان")
            product_desc = st.text_input("شرح کد محصول")
            non_bill_reason = st.text_input("دلیل عدم صورت حساب")
        with c3:
            approver = st.selectbox("تایید کننده", APPROVERS)

        submitted = st.form_submit_button("✅ ثبت در کدها")
        if submitted:
            new_row = pd.DataFrame([{
                "کد پرونده یا کد پروژه": code_case_proj,
                "موکل یا عنوان": client_title,
                "کد محصول": product_code,
                "شرح کد محصول": product_desc,
                "افراد": persons,
                "دلیل عدم صورت حساب": non_bill_reason,
                "تایید کننده": approver
            }])
            codes_df = pd.concat([codes_df, new_row], ignore_index=True)
            codes_df.to_csv(CODES_FILE, index=False)
            st.success("رکورد کدها ذخیره شد.")

    st.dataframe(codes_df, use_container_width=True)

# -------------------------
# TAB 3 - ثبت زمان
# -------------------------
with tabs[2]:
    st.markdown("### تب ثبت زمان")

    with st.form("time_form", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            date_shamsi = st.text_input("تاریخ (شمسی)", placeholder="مثال: ۱۴۰۵/۰۵/۲۶")
            month = st.selectbox("ماه", MONTHS_FA, index=4)
            week = st.selectbox("هفته", [1, 2, 3, 4, 5], index=0)
            recorder = st.text_input("ثبت‌کننده")
        with c2:
            from_time = st.text_input("از ساعت", placeholder="09:00")
            to_time = st.text_input("تا ساعت", placeholder="10:15")
            case_proj = st.text_input("کد پرونده / پروژه")
            client = st.text_input("موکل")
        with c3:
            product_code = st.text_input("کد محصول")
            activity_code = st.selectbox("کد فعالیت", ACTIVITY_CODES)
            work_desc = st.text_area("شرح کار", height=100)
            non_bill_reason = st.text_input("دلیل عدم صورت‌حساب")
        with c4:
            approver_t = st.selectbox("تأییدکننده", APPROVERS, key="approver_time")
            review = st.selectbox("بررسی", ["کامل", "ناقص"], index=0)
            st.markdown("**قابل صورت‌حساب؟**")
            billable_auto = BILLABLE_MAP.get(activity_code, "خیر")
            st.write(f"`{billable_auto}`")

        submitted_time = st.form_submit_button("✅ ثبت زمان")
        if submitted_time:
            t1 = parse_time_str(from_time)
            t2 = parse_time_str(to_time)
            if not t1 or not t2:
                st.error("فرمت ساعت نامعتبر است. مثل 09:00")
            else:
                duration = (t2 - t1).total_seconds() / 3600
                if duration < 0:
                    duration += 24  # عبور از نیمه شب
                duration = round_to_0_1(duration)

                new_row = pd.DataFrame([{
                    "تاریخ (شمسی)": date_shamsi,
                    "ماه": month,
                    "هفته": week,
                    "ثبت‌کننده": recorder,
                    "از ساعت": from_time,
                    "تا ساعت": to_time,
                    "مدت (ساعت)": duration,
                    "کد پرونده / پروژه": case_proj,
                    "موکل": client,
                    "کد محصول": product_code,
                    "کد فعالیت": activity_code,
                    "شرح کار": work_desc,
                    "قابل صورت‌حساب؟": billable_auto,
                    "دلیل عدم صورت‌حساب": non_bill_reason,
                    "تأییدکننده": approver_t,
                    "بررسی": review
                }])
                time_df = pd.concat([time_df, new_row], ignore_index=True)
                time_df.to_csv(TIME_FILE, index=False)
                st.success(f"ثبت شد. مدت محاسبه‌شده: {duration} ساعت")

    st.dataframe(time_df, use_container_width=True)

# -------------------------
# TAB 4 - مراجعات
# -------------------------
with tabs[3]:
    st.markdown("### تب ثبت مراجعات")
    with st.form("leads_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            d = st.text_input("تاریخ (شمسی)", key="lead_date")
            m = st.selectbox("ماه", MONTHS_FA, key="lead_month", index=4)
            call_time = st.text_input("ساعت تماس", placeholder="11:30")
            caller_name = st.text_input("نام تماس‌گیرنده")
        with c2:
            phone = st.text_input("شماره تماس")
            channel = st.text_input("منبع / کانال")
            pcode = st.text_input("کد محصول", key="lead_pcode")
            one_line_subject = st.text_input("موضوع در یک خط")
        with c3:
            requested_slot = st.text_input("ساعت یا روز درخواستی برای مشاوره")
            result = st.text_input("نتیجه")
            written_offer_date = st.text_input("تاریخ ارسال پیشنهاد کتبی")

        submitted_lead = st.form_submit_button("✅ ثبت مراجعه")
        if submitted_lead:
            new_row = pd.DataFrame([{
                "تاریخ (شمسی)": d,
                "ماه": m,
                "ساعت تماس": call_time,
                "نام تماس‌گیرنده": caller_name,
                "شماره تماس": phone,
                "منبع / کانال": channel,
                "کد محصول": pcode,
                "موضوع در یک خط": one_line_subject,
                "ساعت یا روز درخواستی برای مشاوره": requested_slot,
                "نتیجه": result,
                "تاریخ ارسال پیشنهاد کتبی": written_offer_date
            }])
            leads_df = pd.concat([leads_df, new_row], ignore_index=True)
            leads_df.to_csv(LEADS_FILE, index=False)
            st.success("مراجعه ثبت شد.")

    st.dataframe(leads_df, use_container_width=True)

# -------------------------
# TAB 5 - پروژه‌ها
# -------------------------
with tabs[4]:
    st.markdown("### تب پروژه‌ها")
    with st.form("projects_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            pr_code = st.text_input("کد پروژه")
            pr_name = st.text_input("نام پروژه")
            sponsor = st.text_input("حامی (شریک)")
        with c2:
            deliverable = st.text_input("خروجی قابل تحویل")
            deadline = st.text_input("مهلت")
            cap_hours = st.number_input("سقف ساعت ماهانه", min_value=0.0, step=0.1)
        with c3:
            month_year = st.text_input("ماه و سال", placeholder="مثال: مرداد ۱۴۰۵")

        submitted_project = st.form_submit_button("✅ ثبت پروژه")
        if submitted_project:
            new_row = pd.DataFrame([{
                "کد پروژه": pr_code,
                "نام پروژه": pr_name,
                "حامی (شریک)": sponsor,
                "خروجی قابل تحویل": deliverable,
                "مهلت": deadline,
                "سقف ساعت ماهانه": cap_hours,
                "ساعت مصرف‌شده (خودکار)": 0.0,
                "وضعیت (خودکار)": "",
                "ماه و سال": month_year
            }])
            projects_df = pd.concat([projects_df, new_row], ignore_index=True)
            projects_df.to_csv(PROJECTS_FILE, index=False)
            st.success("پروژه ثبت شد.")

    # محاسبه خودکار مصرف پروژه از ثبت زمان برای کد PRO
    proj_view = projects_df.copy()
    if not time_df.empty and not proj_view.empty:
        temp = time_df.copy()
        temp["مدت (ساعت)"] = pd.to_numeric(temp["مدت (ساعت)"], errors="coerce").fillna(0)
        temp_pro = temp[temp["کد فعالیت"] == "PRO"]
        usage = temp_pro.groupby("کد پرونده / پروژه")["مدت (ساعت)"].sum().to_dict()

        consumed_list = []
        status_list = []
        for _, r in proj_view.iterrows():
            code = str(r["کد پروژه"])
            cap = float(r["سقف ساعت ماهانه"]) if str(r["سقف ساعت ماهانه"]).strip() != "" else 0.0
            consumed = round(usage.get(code, 0.0), 1)
            consumed_list.append(consumed)
            if cap <= 0:
                status = "نیازمند تعیین سقف"
            elif consumed <= cap:
                status = "در محدوده"
            else:
                status = "عبور از سقف"
            status_list.append(status)

        proj_view["ساعت مصرف‌شده (خودکار)"] = consumed_list
        proj_view["وضعیت (خودکار)"] = status_list

    st.dataframe(proj_view, use_container_width=True)

# -------------------------
# TAB 6 - داشبورد
# -------------------------
with tabs[5]:
    st.markdown("### داشبورد بهره‌وری")
    st.caption("همه اعداد خودکار از برگه «ثبت زمان» · ورودی جلسه شنبه · فقط دو خانه زرد را تغییر دهید")

    if time_df.empty:
        st.warning("هنوز داده‌ای در «ثبت زمان» ثبت نشده است.")
    else:
        ddf = time_df.copy()
        ddf["مدت (ساعت)"] = pd.to_numeric(ddf["مدت (ساعت)"], errors="coerce").fillna(0)
        ddf["هفته"] = pd.to_numeric(ddf["هفته"], errors="coerce").fillna(0).astype(int)

        months_in_data = [m for m in MONTHS_FA if m in ddf["ماه"].dropna().unique().tolist()]
        if not months_in_data:
            months_in_data = MONTHS_FA

        c1, c2 = st.columns(2)
        with c1:
            selected_month = st.selectbox("ماه", months_in_data, index=max(0, len(months_in_data)-1))
        with c2:
            selected_week = st.selectbox("هفته", [1, 2, 3, 4, 5], index=0)

        def make_summary(df):
            if df.empty:
                cols = ["ثبت‌کننده"] + ACTIVITY_CODES + ["ساعت پرداختی", "بهره‌وری"]
                return pd.DataFrame(columns=cols)

            pivot = df.pivot_table(
                index="ثبت‌کننده",
                columns="کد فعالیت",
                values="مدت (ساعت)",
                aggfunc="sum",
                fill_value=0
            ).reset_index()

            for c in ACTIVITY_CODES:
                if c not in pivot.columns:
                    pivot[c] = 0.0

            pivot["ساعت پرداختی"] = pivot[list(PAID_CODES)].sum(axis=1)
            pivot["بهره‌وری"] = pivot.apply(
                lambda r: (r["BILL"] / r["ساعت پرداختی"] * 100) if r["ساعت پرداختی"] > 0 else 0, axis=1
            )

            pivot = pivot[["ثبت‌کننده"] + ACTIVITY_CODES + ["ساعت پرداختی", "بهره‌وری"]]
            num_cols = ACTIVITY_CODES + ["ساعت پرداختی"]
            pivot[num_cols] = pivot[num_cols].round(1)
            pivot["بهره‌وری"] = pivot["بهره‌وری"].round(1)

            total = {"ثبت‌کننده": "جمع"}
            for c in ACTIVITY_CODES:
                total[c] = round(pivot[c].sum(), 1)
            total_paid = round(pivot["ساعت پرداختی"].sum(), 1)
            total["ساعت پرداختی"] = total_paid
            total["بهره‌وری"] = round((total["BILL"] / total_paid * 100), 1) if total_paid > 0 else 0.0
            pivot = pd.concat([pivot, pd.DataFrame([total])], ignore_index=True)
            return pivot

        weekly_df = ddf[(ddf["ماه"] == selected_month) & (ddf["هفته"] == selected_week)]
        monthly_df = ddf[(ddf["ماه"] == selected_month)]

        weekly_summary = make_summary(weekly_df)
        monthly_summary = make_summary(monthly_df)

        st.markdown("#### هفتگی — ماه و هفته انتخاب‌شده")
        st.dataframe(weekly_summary, use_container_width=True)

        st.markdown("#### ماهانه — کل ماه انتخاب‌شده")
        st.dataframe(monthly_summary, use_container_width=True)

        # KPI ها
        total_bill = monthly_df.loc[monthly_df["کد فعالیت"] == "BILL", "مدت (ساعت)"].sum()
        total_nbc = monthly_df.loc[monthly_df["کد فعالیت"] == "NBC", "مدت (ساعت)"].sum()
        total_pro = monthly_df.loc[monthly_df["کد فعالیت"] == "PRO", "مدت (ساعت)"].sum()
        total_adm = monthly_df.loc[monthly_df["کد فعالیت"] == "ADM", "مدت (ساعت)"].sum()
        total_trn = monthly_df.loc[monthly_df["کد فعالیت"] == "TRN", "مدت (ساعت)"].sum()
        total_brk = monthly_df.loc[monthly_df["کد فعالیت"] == "BRK", "مدت (ساعت)"].sum()

        paid_total = monthly_df[monthly_df["کد فعالیت"].isin(PAID_CODES)]["مدت (ساعت)"].sum()
        team_productivity = (total_bill / paid_total * 100) if paid_total > 0 else 0
        pro_share = (total_pro / paid_total * 100) if paid_total > 0 else 0
        adm_share = (total_adm / paid_total * 100) if paid_total > 0 else 0
        incomplete_rows = monthly_df[monthly_df["بررسی"] == "ناقص"].shape[0]
        leads_count = leads_df[leads_df["ماه"] == selected_month].shape[0] if not leads_df.empty else 0

        kpi = pd.DataFrame([
            ["بهره‌وری کل تیم", f"{team_productivity:.1f}%", "کف بین‌المللی ۳۸٪ (Clio 2025)",
             "در محدوده" if team_productivity >= 38 else "زیر کف بین‌المللی — بررسی شود"],
            ["نشت درآمد — ساعت NBC", f"{total_nbc:.1f}", "هدف: نزدیک صفر",
             "در محدوده" if total_nbc <= 0.2 else "کارِ موکلِ صورت‌حساب‌نشده — دلیل هر سطر بررسی شود"],
            ["سهم پروژه داخلی از ساعت پرداختی", f"{pro_share:.1f}%", "سقف پیشنهادی: ۲۰٪",
             "در محدوده" if pro_share <= 20 else "از سقف پیشنهادی گذشته — منشور و سقف ساعت لازم است"],
            ["سهم اداری از ساعت پرداختی", f"{adm_share:.1f}%", "مدل: حدود ۲۵٪ برای وکیل جوان",
             "در محدوده"],
            ["ساعت آموزش ثبت‌شده", f"{total_trn:.1f}", "دوره کارآموزی: باید دیده شود",
             "در محدوده" if total_trn > 0 else "صفر — آموزش ثبت نشده یا با کد اشتباه ثبت شده"],
            ["استراحت ثبت‌شده", f"{total_brk:.1f}", "الزامی: مطابق دستورالعمل داخلی",
             "در محدوده" if total_brk > 0 else "صفر — استراحت قانونی گرفته نشده یا ثبت نشده"],
            ["سطرهای ناقص", f"{incomplete_rows}", "هدف: صفر",
             "همه سطرها کامل" if incomplete_rows == 0 else "ردیف ناقص وجود دارد"],
            ["سطرهای ثبت‌شده در دفتر مراجعات", f"{leads_count}", "هدف سند ۵: هشت سرنخ در هفته",
             "در محدوده" if leads_count >= 8 else "دفتر مراجعات کم‌ثبت است — نیاز به پیگیری"],
        ], columns=["سنجه", "مقدار", "مرجع / هدف", "قضاوت خودکار"])

        st.markdown("#### سنجه‌های کلیدی — ماه انتخاب‌شده")
        st.dataframe(kpi, use_container_width=True)

        # خروجی اکسل داشبورد
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            weekly_summary.to_excel(writer, sheet_name="Weekly", index=False)
            monthly_summary.to_excel(writer, sheet_name="Monthly", index=False)
            kpi.to_excel(writer, sheet_name="KPI", index=False)

        st.download_button(
            label="📥 دانلود خروجی اکسل داشبورد",
            data=output.getvalue(),
            file_name=f"dashboard_{selected_month}_week{selected_week}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
