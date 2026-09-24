MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB, spec section 5
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
SESSION_TTL_SECONDS = 30 * 60  # analyses live in memory only, spec section 47 privacy principle

CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
