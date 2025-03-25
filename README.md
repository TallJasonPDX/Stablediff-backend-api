# NurseFilter API

A FastAPI backend service that processes images through RunPod with different nurse-themed LoRAs for specialized filter effects.

## 📋 Features

- **Asynchronous Image Processing**: Transform images using RunPod endpoints
- **Synchronous Processing Option**: Support for both async and sync processing modes
- **Object Storage Integration**: Persistent storage for input and output images
- **User Management**: User accounts with quota system
- **Theme Management**: Multiple nurse-themed styles to choose from
- **Job Status Tracking**: Monitor processing status with polling support
- **Webhook Integration**: RunPod webhook support for processing status updates

## 🏗️ Project Structure

```
├── app/                      # Application code
│   ├── repository/          # Database operations
│   ├── routers/            # API route definitions
│   ├── services/           # Business logic services
│   │   ├── runpod.py      # RunPod integration service
│   │   └── job_tracker.py # Job status tracking service
│   ├── utils/             # Utility functions
│   │   └── storage.py     # Object storage operations
│   ├── config.py          # Configuration settings
│   ├── database.py        # Database models and setup
│   ├── dependencies.py    # FastAPI dependencies
│   ├── models.py         # Pydantic models
│   └── security.py       # Authentication logic
├── scripts/               # Utility scripts
├── static/               # Static files
│   ├── uploads/          # Original uploaded images
│   ├── processed/        # Processed output images
│   └── theme_previews/   # Theme preview images
├── main.py              # Application entry point
└── requirements.txt     # Python dependencies
```

## 🔑 API Endpoints

### Image Processing

- `POST /api/images/process-image`
  ```json
  {
    "workflow_name": "string",
    "image": "base64_string",
    "endpointId": "string",
    "waitForResponse": boolean
  }
  ```
  Returns:
  ```json
  {
    "job_id": "string",
    "status": "string",
    "output_image": "string",
    "message": "string"
  }
  ```

- `GET /api/images/job-status/{job_id}`
  Returns job status and result information

### User Management
- `GET /api/user/profile` - Get user profile and quota
- `GET /api/user/me` - Get current user information


## 🚀 Development

Start the development server:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Access OpenAPI documentation at: `/docs` or `/redoc`

## 📄 License

[MIT License](LICENSE)