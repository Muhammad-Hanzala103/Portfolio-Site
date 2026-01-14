# 🚀 Ultimate Industrial Portfolio

![Vercel Deployment](https://img.shields.io/badge/Vercel-Deployed-black?logo=vercel&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-Web%20Framework-blue?logo=flask&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11+-yellow?logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue?logo=postgresql&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

A professional, high-performance portfolio website built with modern **Flask (Python)** and **Industrial-Grade Standards**. This project features a 3D interactive design, banking-level security, and next-generation SEO optimization.

![Project Preview](static/img/meta-image.jpg)

## 🔥 Ultimate Features

### 🎨 Premium UI/UX
-   **3D Interactive Background**: Powered by [Vanta.js](https://www.vantajs.com/) (Net Effect) for a stunning first impression.
-   **Dynamic Light/Dark Mode**: Persists user preference with a smooth toggle transition.
-   **Glassmorphism Design**: Modern frosted glass aesthetics on navbars and cards.
-   **GSAP Animations**: Professional scroll-triggered animations for elements.

### 🛡️ Fortress Security
-   **Rate Limiting**: Brute-force protection on Admin Login (max 5 attempts/minute) using `Flask-Limiter`.
-   **Secure Sessions**: `HttpOnly`, `Secure`, and `SameSite` cookie policies enforced.
-   **CSRF Protection**: All forms protected against Cross-Site Request Forgery.

### ⚡ Extreme Performance
-   **Auto-WebP Conversion**: Uploaded images are automatically converted to optimized **WebP** format (30-50% size reduction).
-   **Asynchronous Emails**: Contact form sends emails in the background without freezing the UI.
-   **Lazy Loading**: Native lazy loading for off-screen images.

### 🔍 Advanced SEO
-   **JSON-LD Structured Data**:
    -   `WebSite` Schema for search box eligibility.
    -   `Person` Schema for Knowledge Graph.
    -   `SoftwareSourceCode` Schema for project details (rich snippets).
    -   `BlogPosting` Schema for articles.
-   **Dynamic Sitemap**: `/sitemap.xml` automatically auto-updates with new database content.
-   **Robots.txt**: Fully configured for crawlers.

---

## 🛠️ Technology Stack

-   **Backend**: Flask, SQLAlchemy, Flask-Login, Flask-Admin
-   **Frontend**: HTML5, CSS3 (Variables), JavaScript (ES6+), Jinja2
-   **Database**: PostgreSQL (Production), SQLite (Dev)
-   **Libraries**:
    -   `Vanta.js` & `Three.js` (3D Backgrounds)
    -   `GSAP` (Animations)
    -   `Flask-Limiter` (Security)
    -   `Pillow` (Image Processing)

---

## 🚀 Getting Started

### Prerequisites
-   Python 3.10+
-   Git

### Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/Muhammad-Hanzala103/portfolio-site.git
    cd portfolio-site
    ```

2.  **Create a Virtual Environment**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # Mac/Linux
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Environment Setup**
    Create a `.env` file in the root directory:
    ```ini
    SECRET_KEY=your_secure_random_key
    DATABASE_URL=sqlite:///app.db  # Or PostgreSQL URL
    MAIL_USERNAME=your_email@gmail.com
    MAIL_PASSWORD=your_app_password
    ```

5.  **Run the Application**
    ```bash
    flask run
    # Or
    python app.py
    ```
    Visit `http://localhost:5000`

---

## ☁️ Deployment (Vercel)

This project is optimized for [Vercel](https://vercel.com/) deployment.

1.  **Push to GitHub**.
2.  **Import to Vercel**: Connect your repository.
3.  **Configure Environment Variables**: Add `DATABASE_URL` (Must be PostgreSQL, e.g., Supabase/Neon), `SECRET_KEY`, etc.
4.  **Deploy**: Vercel will automatically detect `vercel.json` and build your Python app.

See `deploy.md` for a detailed guide.

---

## 👨‍💻 Author

**Muhammad Hanzala**
-   Full Stack Developer & UI/UX Designer
-   [LinkedIn](https://www.linkedin.com/in/muhammad-hanzala-47439328a/)
-   [GitHub](https://github.com/Muhammad-Hanzala103)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
