# intellimaKG_demo.py
import streamlit as st
from pathlib import Path
import json
from datetime import date, datetime, timedelta

# ----------------- ΡΥΘΜΙΣΕΙΣ -----------------
APP_NAME = "IntellimaKG"
SLOGAN = "Empower your business intelligence"
TRIAL_DAYS = 7
DB_FILE = "trials.json" # τοπικό αρχείο αποθήκευσης trial data
STATIC_LOGO = Path("static") / "logo.png"

# Δημιουργία λίστας έγκυρων demo codes
VALID_DEMOS = ["test123"] + [f"demo{i}" for i in range(1, 51)]

ROOT = Path(__file__).parent

# ----------------- Βοηθητικές Συναρτήσεις -----------------
def db_path():
    return ROOT / DB_FILE

def load_db():
    p = db_path()
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def save_db(d):
    p = db_path()
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

def iso_today():
    return date.today().isoformat()

def ensure_entry(db, code):
    code = code.lower()
    if code not in db:
        db[code] = {
            "first_use": None, # ISO date string ή None
            "uses": 0
        }
    return db

def register_use(db, code):
    code = code.lower()
    db = ensure_entry(db, code)
    if db[code]["first_use"] is None:
        db[code]["first_use"] = iso_today()
    db[code]["uses"] = db[code].get("uses", 0) + 1
    save_db(db)
    return db

def set_first_use(db, code, iso_date):
    code = code.lower()
    db = ensure_entry(db, code)
    db[code]["first_use"] = iso_date
    save_db(db)
    return db

def days_since_first_use(db, code):
    code = code.lower()
    db = ensure_entry(db, code)
    fu = db[code].get("first_use")
    if not fu:
        return None
    try:
        d = datetime.fromisoformat(fu).date()
        return (date.today() - d).days
    except Exception:
        return None

def trial_active(db, code):
    code = code.lower()
    if code == "test123":
        return True
    ds = days_since_first_use(db, code)
    if ds is None:
        return True # αν δεν έχει first_use, θεωρούμε πρώτη χρήση επιτρεπτή
    return ds < TRIAL_DAYS

def trial_remaining_days(db, code):
    if code.lower() == "test123":
        return None
    ds = days_since_first_use(db, code)
    if ds is None:
        return TRIAL_DAYS
    rem = TRIAL_DAYS - ds
    return max(0, rem)

# ----------------- Streamlit UI -----------------
st.set_page_config(page_title=f"{APP_NAME} Demo", page_icon="🛍️", layout="centered")

# watermark top-right
st.markdown("""
<style>
.stApp > header {visibility: hidden;}
.watermark {
    position: fixed;
    top: 10px;
    right: 14px;
    font-size: 12px;
    color: #666;
    background: rgba(255,255,255,0.85);
    padding: 6px 8px;
    border-radius: 6px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    z-index: 9999;
}
.center-logo {
    display:flex; align-items:center; justify-content:center; flex-direction:column;
    margin-top: 8px; margin-bottom: 6px;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="watermark">Powered by IntellimaKG</div>', unsafe_allow_html=True)

# header: centered logo + slogan
slogan = f"<div class='slogan'>{SLOGAN}</div>"
logo_tag = ""
if (ROOT / STATIC_LOGO).exists():
    logo_tag = f'<img src="{STATIC_LOGO.as_posix()}" style="width:140px; height:auto; border-radius:10px; box-shadow: 0 2px 6px rgba(0,0,0,0.08);" />'
header_html = f"""
<div class="center-logo">
  {logo_tag}
  <div style="font-family: Inter, Arial; margin-top:10px; text-align:center;">
    <div style="font-size:28px; font-weight:800; color:#111;">{APP_NAME}</div>
    <div style="color:#004aad; font-size:14px; margin-top:6px;">{SLOGAN}</div>
  </div>
</div>
<hr style="margin-top:8px; margin-bottom:18px; border:none; height:1px; background:#eee;">
"""
st.markdown(header_html, unsafe_allow_html=True)

st.markdown(
    "<div style='text-aling:center; color:#444; background-color:#f2f2f2;"
    "padding:12px; border-radius:8px; font-size:16px;'>"
    "Χρησιμοποιήστε τον demo κωδικό που σας δόθηκε.<br>"
    "Καλή σας απόλαυση!"
    "</div>"
    unsafe_allow_html=True)


# code input
code_input = st.text_input("🔐 Εισάγετε demo κωδικό:", type="password")

db = load_db()

if code_input:
    code = code_input.strip().lower()
    if code not in VALID_DEMOS:
        st.error("❌ Μη έγκυρος demo κωδικός. Επικοινωνήστε για δοκιμαστικό κωδικό.")
    else:
        # ADMIN separate view (test123)
        if code == "test123":
            # register admin use but do not change first_use for test123
            db = ensure_entry(db, code)
            db[code]["uses"] = db[code].get("uses", 0) + 1
            save_db(db)

            st.success("✅ Είσοδος Admin (test123). Εμφανίζεται το Admin Panel κάτω από αυτό το μήνυμα.")
            st.markdown("### 🔧 Admin Panel")
            st.write("Εδώ βλέπετε όλα τα demo, ημερομηνίες πρώτης χρήσης, μέρες που πέρασαν και κατάσταση trial.")
            # build table
            table = []
            for d in [f"demo{i}" for i in range(1,51)] + ["test123"]:
                entry = db.get(d, {"first_use": None, "uses": 0})
                fu = entry.get("first_use")
                days = days_since_first_use(db, d)
                remaining = trial_remaining_days(db, d)
                status = "ACTIVE" if trial_active(db, d) else "EXPIRED"
                table.append({
                    "code": d,
                    "first_use": fu or "-",
                    "days_passed": days if days is not None else "-",
                    "remaining_days": remaining if remaining is not None else "∞",
                    "status": status,
                    "uses": entry.get("uses", 0)
                })
            st.table(table)

            st.markdown("### Διευθύνσεις ενεργειών (Admin)")
            st.write("Επιλέξτε έναν κωδικό και κάντε reset (ξεκινάει trial σήμερα) ή force-expire (το κάνει ληγμένο).")
            col1, col2 = st.columns(2)
            with col1:
                sel = st.selectbox("Επίλεξε κωδικό για ενέργεια:", [f"demo{i}" for i in range(1,51)])
            with col2:
                action = st.selectbox("Ενέργεια:", ["reset_to_today", "force_expire", "clear_record"])

            if st.button("Εκτέλεση ενέργειας"):
                if action == "reset_to_today":
                    db = set_first_use(db, sel, iso_today())
                    st.success(f"Ο κωδικός {sel} επαναφέρθηκε: first_use = {iso_today()}")
                elif action == "force_expire":
                    old = (date.today() - timedelta(days=TRIAL_DAYS + 1)).isoformat()
                    db = set_first_use(db, sel, old)
                    st.success(f"Ο κωδικός {sel} ορίστηκε ως ληγμένος (first_use = {old})")
                elif action == "clear_record":
                    if sel in db:
                        db[sel] = {"first_use": None, "uses": 0}
                        save_db(db)
                        st.success(f"Ο κωδικός {sel} καθαρίστηκε (θα θεωρηθεί πρώτη χρήση την επόμενη είσοδο).")
                # refresh DB & table
                db = load_db()

            st.markdown("### Export / Εφεδρικό αρχείο")
            if st.button("Κατέβασμα trials.json"):
                txt = json.dumps(db, ensure_ascii=False, indent=2)
                st.download_button("Download trials.json", txt.encode("utf-8"), file_name="trials.json")

            st.markdown("---")
            st.caption("Μόνο εσείς (admin) βλέπετε αυτή τη σελίδα. Προσοχή: αν διαγράψετε το trials.json οι trials θα χάσουν το ιστορικό τους.")
        else:
            # normal demo user
            # register first use if needed (but do not reset existing)
            db = ensure_entry(db, code)
            # if first_use is None -> register today as first use
        if db[code]["first_use"] is None:
            db = register_use(db, code) # will set first_use = today and increment uses
        else:
            # increment uses count only
            db[code]["uses"] = db[code].get("uses", 0) + 1
            save_db(db)

        # check trial status
        if not trial_active(db, code):
            st.warning("⚠️ Η δοκιμαστική περίοδος των 7 ημερών για αυτόν τον κωδικό έχει λήξει.")
            st.write(f"- **Κωδικός:** {code}")
            st.write(f"- **Ημερομηνία πρώτης χρήσης:** {db[code].get('first_use')}")
            st.info("Επικοινωνήστε με την ομάδα IntellimaKG για ενεργοποίηση πλήρους πρόσβασης.")
        else:
            # show demo interface
            rem = trial_remaining_days(db, code)
            st.success(f"✅ Επιτυχής είσοδος: **{code}** — Trial ενεργό.")
            if rem is not None:
                st.info(f"⏳ Απομένουν περίπου **{rem}** ημέρες trial για αυτόν τον κωδικό.")

            st.markdown("## 🛒 E-shop Content Assistant — Demo")
            st.write("Δοκιμαστική λειτουργία: δημιουργία περιγραφής προϊόντος, SEO τίτλων & προτάσεων για social media.")

            # product inputs
            product_name = st.text_input("🔑 Όνομα προϊόντος:")
            category = st.selectbox("Κατηγορία προϊόντος:", ["Ρούχα", "Παπούτσια", "Καλλυντικά", "Ηλεκτρικά", "Βιβλία", "Άλλα"])
            keywords = st.text_input("Λέξεις-κλειδιά (π.χ. βαμβάκι, ανθεκτικό, επίσημο):")
            tone = st.selectbox("Ύφος περιγραφής:", ["Επαγγελματικό", "Φιλικό", "Σύντομο/Πρωτότυπο", "Περιγραφικό/Λεπτομερές"])

            if st.button("✍️ Δημιουργία Δείγματος Περιγραφής"):
                if not product_name.strip():
                    st.warning("Παρακαλώ συμπληρώστε όνομα προϊόντος για να δημιουργήσουμε δείγμα.")
                else:
                    title = f"{product_name} — {category} | Ποιότητα & αξία"
                    description_lines = [
                        f"Ανακαλύψτε το {product_name}, ιδανικό για {category.lower()} με χαρακτηριστικά: {keywords}.",
                        f"Ύφος: {tone}. Σχεδιασμένο για άνεση, ποιότητα και μοντέρνα εμφάνιση.",
                        "Κατάλληλο για καθημερινή χρήση και ιδανικό για δώρο.",
                        "Τεχνικά χαρακτηριστικά και οδηγίες φροντίδας: αναγράφονται στο e-shop."
                    ]
                    description = "\n\n".join(description_lines)

                    tags = []
                    if keywords:
                        for k in [s.strip() for s in keywords.split(",") if s.strip()]:
                            tags.append(f"#{k.replace(' ', '')}")
                    tags = ["#" + category.replace(" ", "")] + tags
                    tags_str = " ".join(tags[:15]) if tags else f"#{product_name.replace(' ', '')}"

                    st.subheader("📝 Δείγμα Τίτλου")
                    st.write(title)

                    st.subheader("📝 Δείγμα Περιγραφής")
                    st.write(description)

                    st.subheader("🏷️ Προτεινόμενα Hashtags")
                    st.code(tags_str)

                    st.success("✅ Demo περιγραφή δημιουργήθηκε. Στην πλήρη έκδοση: πολλαπλές επιλογές, SEO optimization, εξαγωγή σε CSV/PDF, και αυτόματες μεταφράσεις.")

            st.markdown("### Άμεση Εξαγωγή (Demo)")
            if st.button("📥 Κατέβασμα περιγραφής ως .txt (demo)"):
                txt = f"Title: {product_name}\n\nDescription:\n{(product_name and (product_name + ' sample description')) or '—'}\n\nTags: {keywords}"
                st.download_button("Download description (.txt)", txt.encode("utf-8"), file_name=f"{(product_name or 'product')}_description.txt")

# Footer
st.markdown("---")
st.caption("© 2025 IntellimaKG | Demo Version – All rights reserved.")