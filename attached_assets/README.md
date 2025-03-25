
# Image Processing API with RunPod and Object Storage

A TypeScript/Node.js Express application that processes images using RunPod's API and stores them using Replit's Object Storage.

## Architecture

### Backend Components

- **Express Server**: Node.js/TypeScript server handling API requests and file management
- **RunPod Integration**: Processes images using AI models via RunPod's API
- **Object Storage**: Manages persistent file storage using Replit's Object Storage

### Project Structure

```
├── server/
│   ├── object-storage.ts   # Object Storage client and file operations
│   ├── routes.ts          # API endpoints and RunPod integration
│   └── index.ts          # Express server setup
├── client/               # React frontend application
├── shared/              # Shared TypeScript types and schemas
├── input_images/        # Local directory for input image processing
└── output_images/       # Local directory for processed images
```

## Key Features

### Object Storage Integration (`object-storage.ts`)

Handles file storage operations using Replit's Object Storage:
- `saveBase64ImageToStorage`: Saves base64-encoded images
- `objectExists`: Verifies object existence
- `getObjectUrl`: Retrieves object URLs

### RunPod Integration (`routes.ts`)

Manages image processing through RunPod's API:
- Synchronous and asynchronous processing modes
- Job status tracking and webhook support
- Automatic image storage before/after processing

## API Endpoints

- `POST /api/process-image`: Submit images for processing
- `GET /api/job-status/:jobId`: Check processing status
- `POST /api/webhook/runpod`: Webhook for async job completion

## Environment Setup

Required environment variables:
- `RUNPOD_API_KEY`: Authentication for RunPod API access

## Running the Application

The application runs on port 5000 and is configured to use npm scripts:
- Development: `npm run dev`
- Production: `npm run build && npm run start`
