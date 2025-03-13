
# NurseFilter API

A FastAPI backend service that processes images through Stable Diffusion with different nurse-themed LoRAs for specialized filter effects.

## 📋 Features

- **Image Processing**: Transform images using SDXL Turbo with nurse-themed LoRAs
- **User Management**: User accounts with quota system
- **Instagram Integration**: Authentication via Instagram OAuth
- **Theme Management**: Multiple nurse-themed styles to choose from

## 🏗️ Project Structure

```
├── app/                      # Application code
│   ├── repository/           # Database operations
│   ├── routers/              # API route definitions
│   ├── services/             # Business logic services
│   ├── config.py             # Configuration settings
│   ├── database.py           # Database models and setup
│   ├── dependencies.py       # FastAPI dependencies
│   ├── models.py             # Pydantic models
│   └── security.py           # Authentication logic
├── sd_models/                # Stable Diffusion models
│   └── loras/                # Theme-specific LoRA weights
├── static/                   # Static files
│   ├── uploads/              # Original uploaded images
│   ├── processed/            # Processed output images
│   └── theme_previews/       # Theme preview images
├── main.py                   # Application entry point
├── Dockerfile                # Docker configuration
└── requirements.txt          # Python dependencies
```

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- SDXL Turbo model
- Nurse-themed LoRA files (see `sd_models/loras/README.md`)
- Instagram OAuth credentials (for Instagram integration)

### Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables (see Configuration section)
4. Place SDXL Turbo model in `sd_models/`
5. Place nurse-themed LoRA files in `sd_models/loras/`

### Running the Server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## ⚙️ Configuration

The application uses environment variables for configuration, which can be set in a `.env` file:

- `SECRET_KEY`: JWT secret key
- `DATABASE_URL`: SQLite database URL (default: `sqlite:///./nursefilter.db`)
- `SD_MODEL_PATH`: Path to SDXL Turbo model
- `SD_LORA_DIR`: Directory containing LoRA weights
- `INSTAGRAM_CLIENT_ID`: Instagram OAuth client ID
- `INSTAGRAM_CLIENT_SECRET`: Instagram OAuth client secret
- `INSTAGRAM_REDIRECT_URI`: Instagram OAuth redirect URI
- `INSTAGRAM_REQUIRED_FOLLOW`: Instagram account users should follow
- `DEFAULT_IMAGE_QUOTA`: Default image processing quota
- `FOLLOWER_IMAGE_QUOTA`: Quota for users following required Instagram account

## 🔑 API Endpoints

### Authentication

- `POST /api/auth/token` - Login with username/password
- `POST /api/auth/instagram-login` - Handle Instagram OAuth flow
- `GET /api/auth/check-follow` - Check if user follows specified Instagram page

### User Management

- `GET /api/user/profile` - Get user profile and quota
- `GET /api/user/history` - Get user's processed image history

### Image Processing

- `POST /api/images/process` - Process image with theme
  - Parameters:
    - `input_image`: File
    - `theme`: Theme identifier
    - `strength`: Float (0.0-1.0) optional
- `GET /api/images/{image_id}` - Get processed image

### Theme Management

- `GET /api/themes` - List available themes and descriptions

## 🎨 Available Themes

1. **Classic Nurse** - Traditional nursing attire with a classic, professional look
2. **Modern Healthcare** - Contemporary medical professional style with modern scrubs
3. **Vintage Nurse** - Retro nursing style inspired by mid-20th century healthcare
4. **Anime Nurse** - Stylized anime-inspired nurse character design
5. **Future Medical** - Futuristic healthcare professional with advanced tech elements

## 🔒 Authentication Flow

1. Users authenticate via Instagram OAuth
2. Application verifies if user follows required Instagram account
3. JWT token issued for authenticated users
4. Image quota assigned based on follow status

## 🖼️ Image Processing Flow

1. User uploads image and selects theme
2. Service verifies user has sufficient quota
3. Image processed through SDXL Turbo with selected theme LoRA
4. Processed image stored and URL returned
5. User quota decremented

## 💻 Development

### Adding New Themes

Place new LoRA files in `sd_models/loras/` and update the theme list in `app/routers/themes.py`.

### Testing

Run tests with:
```
pytest
```

## 📄 License

[MIT License](LICENSE)
