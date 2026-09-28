# Deployment Guide

This project is designed to be easily deployed to modern cloud platforms like Railway, Render, or Heroku. The recommended platform for this project is **Railway** due to its easy PostgreSQL provisioning and continuous deployment features.

## Prerequisites
- A Railway account (or similar provider).
- A Razorpay Test Mode account (for Payment Gateway).
- A Meta Developer account (for WhatsApp API credentials).
- An OpenAI API Key.

## 1. Database Setup
1. Provision a PostgreSQL database instance on your chosen platform.
2. Obtain the `DATABASE_URL`. Ensure it uses the `postgresql://` protocol.

## 2. Backend Deployment (FastAPI)
1. Set the deployment root directory to `backend/`.
2. Add the following Environment Variables to the Backend service:
   - `DATABASE_URL` (from step 1)
   - `OPENAI_API_KEY`
   - `RAZORPAY_KEY_ID`
   - `RAZORPAY_KEY_SECRET`
   - `WHATSAPP_ACCESS_TOKEN` (if using real WhatsApp API)
3. Set the start command to:
   ```bash
   alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
   *(This ensures database migrations run before the app starts)*

## 3. Frontend Deployment (React + Vite)
1. Set the deployment root directory to `frontend/`.
2. Ensure you set the environment variable for the backend API URL. For Vite, this is typically `VITE_API_URL`, but our code currently uses an axios default. You should configure it to point to your deployed backend URL.
3. Build command: `npm run build`
4. Start command/Output directory: `dist`

## 4. Webhooks
After the backend is deployed:
1. Go to your Razorpay Dashboard.
2. Add a new webhook pointing to `https://<YOUR-BACKEND-DOMAIN>/api/checkout/webhook/razorpay`.
3. Select the `payment.captured` event.
4. Save the webhook.

## 5. First Run & Seeding
Once the backend is up and running, you can seed the initial products and categories by running the seed script manually on the deployed environment:
```bash
python -m app.seed
```
This will populate the tech store with 14 products across 11 categories.

## Architecture Notes
- The background job (APScheduler) for Abandoned Cart recovery runs continuously within the FastAPI application lifecycle. In a heavily scaled multi-instance deployment, consider moving this to a dedicated worker (e.g., Celery) to prevent duplicate runs, but for this demo, the in-process scheduler is sufficient.
