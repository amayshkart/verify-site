import os
import sqlite3
from flask import Flask, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change-this-in-production-xyz')

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')
ADMIN_USER = os.environ.get('ADMIN_USER', 'admin')
ADMIN_PASS = os.environ.get('ADMIN_PASS', 'admin123')

# ---------------- Database ----------------
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS certificates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        national_id TEXT UNIQUE NOT NULL,
        student_name TEXT NOT NULL,
        degree TEXT NOT NULL,
        field TEXT NOT NULL,
        university TEXT NOT NULL,
        year TEXT NOT NULL,
        status TEXT DEFAULT 'valid'
    )''')
    samples = [
        ('0012345678', 'علی رضایی', 'کارشناسی', 'مهندسی کامپیوتر', 'دانشگاه تهران', '1400'),
        ('0098765432', 'مریم احمدی', 'کارشناسی ارشد', 'حقوق', 'دانشگاه شهید بهشتی', '1402'),
    ]
    for s in samples:
        try:
            conn.execute('''INSERT INTO certificates 
                (national_id, student_name, degree, field, university, year, status)
                VALUES (?,?,?,?,?,?,?)''', (*s, 'valid'))
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    conn.close()

# ---------------- Layout (HTML) ----------------
BASE_HTML = '''<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
* {{ box-sizing: border-box; font-family: Tahoma, sans-serif; }}
body {{ margin: 0; background: #f4f6f9; color: #222; }}
.container {{ max-width: 1000px; margin: 0 auto; padding: 0 16px; }}
header {{ background: #1e3a8a; color: #fff; padding: 14px 0; }}
header .container {{ display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }}
header a {{ color: #fff; text-decoration: none; }}
header nav a {{ margin-left: 16px; opacity: .9; }}
.brand {{ font-weight: bold; font-size: 16px; }}
.banner {{ background: #fef3c7; color: #92400e; text-align: center; padding: 8px; font-size: 13px; }}
main {{ padding: 24px 0; }}
.card {{ background: #fff; padding: 24px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,.06); }}
.card.small {{ max-width: 420px; margin: 0 auto; }}
h1 {{ margin-top: 0; font-size: 22px; }}
h2 {{ font-size: 18px; margin-top: 24px; border-bottom: 1px solid #eee; padding-bottom: 6px; }}
label {{ display: block; margin: 12px 0 6px; font-size: 14px; }}
input, select, button {{ font-family: inherit; font-size: 14px; }}
input, select {{ width: 100%; padding: 10px; border: 1px solid #cbd5e1; border-radius: 8px; }}
button {{ margin-top: 14px; padding: 10px 22px; background: #1e3a8a; color: #fff; border: none; border-radius: 8px; cursor: pointer; }}
.btn {{ display: inline-block; margin-top: 14px; padding: 10px 22px; background: #1e3a8a; color: #fff; text-decoration: none; border-radius: 8px; }}
.btn.danger {{ background: #dc2626; }}
.btn.small {{ padding: 4px 10px; font-size: 12px; margin: 0; }}
.alert {{ background: #dbeafe; color: #1e40af; padding: 10px 14px; border-radius: 8px; margin-bottom: 12px; }}
.error {{ background: #fee2e2; color: #991b1b; padding: 14px; border-radius: 8px; margin-bottom: 14px; }}
.ok {{ background: #dcfce7; color: #166534; padding: 14px; border-radius: 8px; margin-bottom: 14px; font-weight: bold; }}
.info {{ width: 100%; border-collapse: collapse; margin-top: 14px; }}
.info th, .info td {{ padding: 10px; border-bottom: 1px solid #eee; text-align: right; }}
.info th {{ width: 180px; color: #555; background: #f8fafc; }}
.table {{ width: 100%; border-collapse: collapse; margin-top: 14px; font-size: 13px; }}
.table th, .table td {{ padding: 8px; border-bottom: 1px solid #eee; text-align: right; }}
.table thead {{ background: #f1f5f9; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; align-items: end; }}
.grid button {{ margin-top: 0; }}
.hint {{ color: #64748b; font-size: 13px; margin-top: 10px; }}
footer {{ text-align: center; color: #64748b; font-size: 13px; padding: 24px 0; }}
</style>
</head>
<body>
<header>
  <div class="container">
    <a href="/" class="brand">🎓 سامانه استعلام مدرک (نمونه آموزشی)</a>
    <nav><a href="/">استعلام</a><a href="/admin">پنل ادمین</a></nav>
  </div>
</header>
<div class="banner">این سایت یک نمونه آموزشی است و به هیچ سامانه رسمی متصل نیست.</div>
<main class="container">{body}</main>
<footer class="container">ساخته‌شده برای تمرین — Flask + SQLite</footer>
</body>
</html>'''

def render(title, body, flash_html=''):
    return BASE_HTML.format(title=title, body=flash_html + body)

def flash_box():
    msgs = []
    if '_flashes' in session:
        for m in session.pop('_flashes'):
            msgs.append(f'<div class="alert">{m}</div>')
    return ''.join(msgs)

# ---------------- Routes ----------------
@app.route('/')
def index():
    body = '''
    <div class="card">
      <h1>استعلام مدرک تحصیلی</h1>
      <p>برای بررسی صحت مدرک، کد ملی دانش‌آموخته را وارد کنید.</p>
      <form action="/verify" method="post">
        <label>کد ملی</label>
        <input type="text" name="national_id" placeholder="مثلاً 0012345678" required>
        <button type="submit">استعلام</button>
      </form>
      <p class="hint">کدهای نمونه: 0012345678 — 0098765432</p>
    </div>'''
    return render('استعلام مدرک', body)

@app.route('/verify', methods=['POST'])
def verify():
    nid = request.form.get('national_id', '').strip()
    if not nid:
        body = '<div class="card"><div class="error">❌ کد ملی را وارد کنید.</div><a href="/" class="btn">بازگشت</a></div>'
        return render('نتیجه', body)
    conn = get_db()
    row = conn.execute('SELECT * FROM certificates WHERE national_id=?', (nid,)).fetchone()
    conn.close()
    if row:
        status = 'معتبر' if row['status'] == 'valid' else 'باطل'
        body = f'''
        <div class="card">
          <div class="ok">✅ مدرک معتبر است</div>
          <table class="info">
            <tr><th>نام</th><td>{row['student_name']}</td></tr>
            <tr><th>مقطع</th><td>{row['degree']}</td></tr>
            <tr><th>رشته</th><td>{row['field']}</td></tr>
            <tr><th>دانشگاه</th><td>{row['university']}</td></tr>
            <tr><th>سال فارغ‌التحصیلی</th><td>{row['year']}</td></tr>
            <tr><th>وضعیت</th><td>{status}</td></tr>
          </table>
          <a href="/" class="btn">استعلام جدید</a>
        </div>'''
    else:
        body = '<div class="card"><div class="error">❌ مدرکی با این کد ملی یافت نشد.</div><a href="/" class="btn">بازگشت</a></div>'
    return render('نتیجه استعلام', body)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        if u == ADMIN_USER and p == ADMIN_PASS:
            session['admin'] = True
            return redirect(url_for('admin'))
        flash('نام کاربری یا رمز اشتباه است.')
        return redirect(url_for('admin_login'))
    body = '''
    <div class="card small">
      <h1>ورود ادمین</h1>
      <form method="post">
        <label>نام کاربری</label><input name="username" required>
        <label>رمز عبور</label><input name="password" type="password" required>
        <button type="submit">ورود</button>
      </form>
      <p class="hint">پیش‌فرض: admin / admin123</p>
    </div>'''
    return render('ورود ادمین', body, flash_box())

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    conn = get_db()
    if request.method == 'POST':
        data = (
            request.form['national_id'], request.form['student_name'],
            request.form['degree'], request.form['field'],
            request.form['university'], request.form['year'],
            request.form['status'],
        )
        try:
            conn.execute('''INSERT INTO certificates 
                (national_id, student_name, degree, field, university, year, status)
                VALUES (?,?,?,?,?,?,?)''', data)
            conn.commit()
            flash('مدرک ثبت شد.')
        except sqlite3.IntegrityError:
            flash('این کد ملی قبلاً ثبت شده.')
        conn.close()
        return redirect(url_for('admin'))
    certs = conn.execute('SELECT * FROM certificates ORDER BY id DESC').fetchall()
    conn.close()
    rows = ''.join(f'''
      <tr>
        <td>{c['id']}</td><td>{c['national_id']}</td><td>{c['student_name']}</td>
        <td>{c['degree']}</td><td>{c['field']}</td><td>{c['university']}</td>
        <td>{c['year']}</td><td>{'معتبر' if c['status']=='valid' else 'باطل'}</td>
        <td><a href="/admin/delete/{c['id']}" class="btn danger small">حذف</a></td>
      </tr>''' for c in certs)
    body = f'''
    <div class="card">
      <h1>پنل ادمین</h1>
      <a href="/admin/logout" class="btn danger">خروج</a>
      <h2>افزودن مدرک</h2>
      <form method="post" class="grid">
        <input name="national_id" placeholder="کد ملی" required>
        <input name="student_name" placeholder="نام دانش‌آموخته" required>
        <input name="degree" placeholder="مقطع" required>
        <input name="field" placeholder="رشته" required>
        <input name="university" placeholder="دانشگاه" required>
        <input name="year" placeholder="سال" required>
        <select name="status"><option value="valid">معتبر</option><option value="invalid">باطل</option></select>
        <button type="submit">ثبت</button>
      </form>
      <h2>لیست مدارک</h2>
      <table class="table">
        <thead><tr><th>#</th><th>کد ملی</th><th>نام</th><th>مقطع</th><th>رشته</th><th>دانشگاه</th><th>سال</th><th>وضعیت</th><th></th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>'''
    return render('پنل ادمین', body, flash_box())

@app.route('/admin/delete/<int:cid>')
def delete(cid):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    conn = get_db()
    conn.execute('DELETE FROM certificates WHERE id=?', (cid,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

init_db()

if __name__ == '__main__':
    app.run(debug=True)
