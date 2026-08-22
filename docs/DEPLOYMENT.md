# Deployment Guide: Vercel (Frontend) & Render (Backend)

Because VaaniRAG is structured as a monorepo (both `frontend` and `backend` in the same repository), you need to configure your hosting providers to target the correct subdirectories.

## 1. Hosting the Backend on Render

Render is an excellent platform for hosting Python FastAPI backends.

### Steps:
1. **Push your code to GitHub**.
2. Go to [Render.com](https://render.com/) and create a new **Web Service**.
3. Connect your GitHub account and select your VaaniRAG repository.
4. In the service settings:
   - **Name**: `vaanirag-backend` (or similar)
   - **Language**: Python
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port 10000` (Render exposes port 10000 by default)
5. Scroll down to **Advanced** -> **Environment Variables** and add:
   - `SARVAM_API_KEY`
   - `LLM_PROVIDER` (e.g., `openai`)
   - `LLM_API_KEY`
   - `PYTHON_VERSION`: `3.10` (Render defaults to 3.7; you need >= 3.10 for VaaniRAG)
6. Click **Create Web Service**.
7. Once deployed, copy your service URL (e.g., `https://vaanirag-backend.onrender.com`). You will need this for the frontend.

---

## 2. Hosting the Frontend on Vercel

Vercel is optimized for Vite/React applications.

### Steps:
1. Go to [Vercel.com](https://vercel.com/) and click **Add New Project**.
2. Import your VaaniRAG GitHub repository.
3. In the **Configure Project** screen:
   - **Framework Preset**: Vercel should auto-detect **Vite**.
   - **Root Directory**: Click Edit and select the `frontend` folder.
4. Expand the **Environment Variables** section.
5. Add the following variable so the frontend knows where to send API requests:
   - **Name**: `VITE_API_URL`
   - **Value**: `https://<YOUR_RENDER_DOMAIN>/api` *(Make sure to append `/api` to the URL you copied from Render)*.
6. Click **Deploy**.

## CORS Configuration Note
The backend currently has `allow_origins=["*"]` configured in `backend/app/main.py`. This means it will accept requests from your Vercel domain out of the box. For production, you may want to restrict this to exactly your Vercel domain once it's live!
