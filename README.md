# NurseFilter API

A FastAPI backend service that processes images through RunPod with different nurse-themed LoRAs for specialized filter effects.

## 📋 Features

- **Asynchronous Image Processing**: Transform images using RunPod endpoints
- **User Management**: User accounts with quota system
- **Instagram Integration**: Authentication via Instagram OAuth
- **Theme Management**: Multiple nurse-themed styles to choose from
- **Webhook Integration**: RunPod webhook support for processing status updates

## 🏗️ Project Structure

```
├── app/                      # Application code
│   ├── repository/          # Database operations
│   ├── routers/            # API route definitions
│   ├── services/           # Business logic services
│   │   └── runpod.py      # RunPod integration service
│   ├── utils/             # Utility functions
│   ├── config.py          # Configuration settings
│   ├── database.py        # Database models and setup
│   ├── dependencies.py    # FastAPI dependencies
│   ├── models.py          # Pydantic models
│   └── security.py        # Authentication logic
├── scripts/               # Utility scripts
├── static/               # Static files
│   ├── uploads/          # Original uploaded images
│   ├── processed/        # Processed output images
│   └── theme_previews/   # Theme preview images
├── main.py              # Application entry point
└── requirements.txt     # Python dependencies
```

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- PostgreSQL database
- RunPod API key
- Instagram OAuth credentials (for Instagram integration)

### Environment Variables

The application uses environment variables for configuration:

- `SECRET_KEY`: JWT secret key
- `DATABASE_URL`: PostgreSQL connection URL
- `RUNPOD_API_KEY`: RunPod API key for endpoint access
- `RUNPOD_ENDPOINT_ID`: RunPod endpoint identifier
- `INSTAGRAM_CLIENT_ID`: Instagram OAuth client ID
- `INSTAGRAM_CLIENT_SECRET`: Instagram OAuth client secret
- `INSTAGRAM_REDIRECT_URI`: Instagram OAuth redirect URI
- `INSTAGRAM_REQUIRED_FOLLOW`: Instagram account users should follow
- `DEFAULT_IMAGE_QUOTA`: Default image processing quota

## 🔑 API Endpoints

### Authentication
- `POST /api/auth/register` - Register a new user with username/password
- `POST /api/auth/token` - Login with username/password
- `POST /api/auth/instagram-login` - Handle Instagram OAuth flow
- `GET /api/auth/check-follow` - Check if user follows specified Instagram page

### User Management
- `GET /api/user/profile` - Get user profile and quota
- `GET /api/user/history` - Get user's processed image history

### Image Processing

- `POST /api/images/process` - Submit image for processing
  - Parameters:
    - `image_base64`: Base64 encoded image
    - `workflow_id`: Workflow identifier
  - Returns:
    - `request_id`: Unique identifier for tracking processing status

- `GET /api/images/{image_id}` - Get processed image status and result

### Theme Management
- `GET /api/themes` - List available themes and descriptions


### RunPod Integration

The application uses an asynchronous processing flow:

1. User submits image through `/api/images/process`
2. System creates a request record with "pending" status
3. Background service detects pending requests and submits to RunPod
4. RunPod processes the image and calls webhook endpoint
5. System updates request status and stores result

## 🗄️ Database Schema

RunPod requests table includes:
- `id`: Unique identifier
- `user_id`: Associated user
- `workflow_id`: Selected workflow
- `status`: Current status (pending, submitted, processing, completed, failed)
- `runpod_job_id`: RunPod job identifier
- `input_image_url`: Original image
- `output_image_url`: Processed image URL
- `created_at`: Request creation timestamp
- `submitted_at`: RunPod submission timestamp
- `completed_at`: Processing completion timestamp

## 💻 Development

Start the development server:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 📄 License

[MIT License](LICENSE)