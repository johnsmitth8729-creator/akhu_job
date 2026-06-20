# Al-Khwarizmi University Recruitment Portal

A modern, fast, secure, and professional Recruitment Portal for Al-Khwarizmi University. The platform publishes university vacancies, accepts online applications and files, manages HR workflows (status updates, interview schedules), and supports real-time support chats synced with Telegram.

---

## 🛠️ Technology Stack
- **Backend**: Python Flask, SQLAlchemy, Flask-Migrate, Flask-Login, Flask-Babel, Flask-SocketIO
- **Database**: PostgreSQL (Production) / SQLite (Development)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Integrations**: Telegram Bot API for instant alerts and support chat replies, SMTP Email Service

---

## 🚀 Key Features
1. **Multilingual Interface**: Full translation catalogs for English (default), Uzbek (`uz`), and Russian (`ru`).
2. **Interactive Vacancies**: Comprehensive keyword search and faculty/department filtering system.
3. **Secure Document Uploader**: Drag & drop candidate upload tool verifying file types (PDF, Word, Images) and restricting size (under 20MB).
4. **Staff Roles**:
   - **Admin**: User CRUD management, live statistics, system configurations (Telegram APIs, SMTP servers), and scheduled interviews management.
   - **HR Recruiter**: Vacancy management, applicant review, evaluation logs, and scheduling.
5. **Real-time Live Chat**: WebSocket-powered visitor chat widget with automated Telegram notification. Admins and HR can reply directly inside their Telegram group to speak with the website visitor.
6. **Decoupled Academic Structure**: Independent Faculty and Department additions.

---

## 👨‍💻 Developer & Creator Attribution

This platform was designed, engineered, and developed by:

* **Developer**: Omonbayev Jaloliddin
* **Telegram Contact**: [t.me/jaloliddin_omonbaev](https://t.me/jaloliddin_omonbaev)

For any software maintenance, modifications, or inquiries, please contact the developer directly.

---

## 📦 Local Setup Instructions

### 1. Initialize Virtual Environment
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory:
```env
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/akhu_job
```

### 3. Seed Database
Create tables and default users:
```bash
python seed.py
```
* **Admin Account**: `admin` / `admin123`
* **HR Account**: `hr_staff` / `hr123`

### 4. Run Application
```bash
python run.py
```
* Access the portal at `http://127.0.0.1:5000/`.
