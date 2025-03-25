import type { Express, Request, Response, NextFunction } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { insertWorkflowSchema } from "@shared/schema";
import { saveBase64ImageToStorage, getObjectUrl } from "./object-storage";
import fs from "fs";
import path from "path";

// Define job status type
type JobStatus = 'processing' | 'completed' | 'failed';

// Define job data interface
interface JobData {
  status: JobStatus;
  output_image?: string;
  error?: string;
  timestamp: number;
}

// Store processing jobs and their status
const jobs: Record<string, JobData> = {};

export async function registerRoutes(app: Express): Promise<Server> {
  // Ensure object storage folders exist
  try {
    // Create folders for input and output images in object storage
    // These are virtual paths that will be used when storing objects
    console.log('[Object Storage] Setting up image storage folders...');
    
    // Create directories if needed (local directories, not in object storage)
    const inputDir = path.join('.', 'input_images');
    const outputDir = path.join('.', 'output_images');
    
    if (!fs.existsSync(inputDir)) {
      fs.mkdirSync(inputDir, { recursive: true });
      console.log(`[Object Storage] Created input images directory: ${inputDir}`);
    }
    
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
      console.log(`[Object Storage] Created output images directory: ${outputDir}`);
    }
  } catch (error) {
    console.error('[Object Storage] Error setting up storage folders:', error);
  }
  // API endpoint to check job status
  app.get("/api/job-status/:jobId", async (req, res) => {
    try {
      const { jobId } = req.params;
      
      if (!jobId) {
        return res.status(400).json({ 
          message: "Job ID is required" 
        });
      }
      
      // Check if we have the job in our local cache
      if (jobs[jobId]) {
        return res.json(jobs[jobId]);
      }
      
      // If not, check with RunPod API
      const apiKey = process.env.RUNPOD_API_KEY;
      if (!apiKey) {
        return res.status(500).json({
          message: "RunPod API key is not configured"
        });
      }
      
      // The job is submitted to a specific endpoint, so we need the original endpoint ID
      // (not extracted from the job ID, as that's not the correct format)
      
      // Get the endpoint ID from the request query parameter
      const endpointId = req.query.endpointId as string;
      
      if (!endpointId) {
        return res.status(400).json({
          message: "Endpoint ID is required as a query parameter"
        });
      }
      
      const statusUrl = `https://api.runpod.ai/v2/${endpointId}/status/${jobId}`;
      console.log(`[Job Status] Checking job ${jobId} at ${statusUrl}`);
      
      const response = await fetch(statusUrl, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${apiKey}`
        }
      });
      
      // Get raw response text first to help with debugging
      const responseText = await response.text();
      console.log(`[Job Status] Raw response for job ${jobId}: ${responseText.substring(0, 300)}${responseText.length > 300 ? '...' : ''}`);
      
      // Try to parse the JSON response
      let responseData: any;
      try {
        responseData = JSON.parse(responseText);
      } catch (error) {
        console.error(`[Job Status] JSON parse error for job ${jobId}:`, error);
        return res.status(500).json({
          message: "Failed to parse job status response",
          details: responseText.substring(0, 500)
        });
      }
      
      if (!response.ok) {
        return res.status(response.status).json({
          message: `Failed to get job status: ${response.statusText}`,
          details: responseData
        });
      }
      
      if (responseData.status === 'COMPLETED') {
        // Check if we already processed this job to avoid duplicates
        if (jobs[jobId] && jobs[jobId].status === 'completed') {
          console.log(`[Job Status] Job ${jobId} already processed, using cached result`);
          return res.json(jobs[jobId]);
        }
        
        // Determine the output image URL from various possible response formats
        let outputImageUrl = null;
        
        if (responseData.output?.output_image) {
          // Direct output_image field
          outputImageUrl = responseData.output.output_image;
        } else if (responseData.output?.images && responseData.output.images.length > 0) {
          // Images array format
          outputImageUrl = responseData.output.images[0].image || responseData.output.images[0];
        } else if (responseData.output?.message && responseData.output.message.startsWith('data:image/')) {
          // Direct Base64 image in message field
          outputImageUrl = responseData.output.message;
        } else if (responseData.output?.message) {
          // Base64 encoded image in message field without data URI prefix
          outputImageUrl = `data:image/png;base64,${responseData.output.message}`;
        } else if (responseData.output?.all_images && responseData.output.all_images.length > 0) {
          // RunPod all_images format - this includes paths, not URLs
          // For now, we'll try to use the message field which usually contains the Base64 data
          if (responseData.output.message) {
            if (responseData.output.message.startsWith('data:image/')) {
              outputImageUrl = responseData.output.message;
            } else {
              // Assume it's a base64 string
              outputImageUrl = `data:image/png;base64,${responseData.output.message}`;
            }
          }
        }
        
        // Save the output image to storage if we have base64 data
        if (outputImageUrl && (outputImageUrl.startsWith('data:image/') || responseData.output?.message)) {
          try {
            // Use a timestamp for consistent naming across sync and async - don't use prefixes
            const timestamp = Date.now();
            const outputFilename = `${timestamp}.png`;
            
            // Use the base64 data for storage
            const base64Data = outputImageUrl.startsWith('data:image/') 
              ? outputImageUrl 
              : `data:image/png;base64,${responseData.output.message}`;
            
            await saveBase64ImageToStorage(
              base64Data,
              'output_images',
              outputFilename
            );
            console.log(`[Object Storage] Output image saved as ${outputFilename}`);
            
            // Keep the base64 data for the frontend - don't replace with a URL
            // This ensures the frontend always receives base64 data for consistent handling
          } catch (error) {
            console.error('[Object Storage] Failed to save output image:', error);
            // Continue with the original base64 data if storage fails
          }
        }
        
        // Save the completed job status in our cache
        jobs[jobId] = {
          status: 'completed',
          output_image: outputImageUrl,
          timestamp: Date.now()
        };
      } else if (responseData.status === 'FAILED') {
        jobs[jobId] = {
          status: 'failed',
          error: responseData.error || 'Unknown error',
          timestamp: Date.now()
        };
      }
      
      // For async requests from polling, construct a response that the client code expects
      // The client checks several fields for the output image (see ImageTester.tsx)
      return res.json({
        job_id: jobId,
        status: responseData.status,
        // Include the output_image at the root level if available (client checks this first)
        output_image: jobs[jobId]?.output_image || null,
        output: responseData.output,
        error: responseData.error
      });
    } catch (error) {
      console.error("[Job Status Exception]", error);
      return res.status(500).json({ 
        message: error instanceof Error ? error.message : "Unknown error occurred"
      });
    }
  });
  
  // API endpoints for workflow management
  app.get("/api/workflows", async (req, res) => {
    try {
      const workflows = await storage.getWorkflows();
      return res.json(workflows);
    } catch (error) {
      console.error("[Workflows API Error]", error);
      return res.status(500).json({
        message: error instanceof Error ? error.message : "Unknown error occurred"
      });
    }
  });
  
  app.post("/api/workflows", async (req, res) => {
    try {
      const result = insertWorkflowSchema.safeParse(req.body);
      
      if (!result.success) {
        return res.status(400).json({
          message: "Invalid workflow data",
          errors: result.error.errors
        });
      }
      
      // Check if workflow with this value already exists
      const existing = await storage.getWorkflowByValue(result.data.value);
      if (existing) {
        return res.status(409).json({
          message: "A workflow with this value already exists"
        });
      }
      
      const workflow = await storage.createWorkflow(result.data);
      return res.status(201).json(workflow);
    } catch (error) {
      console.error("[Workflow Creation Error]", error);
      return res.status(500).json({
        message: error instanceof Error ? error.message : "Unknown error occurred"
      });
    }
  });
  
  app.get("/api/workflows/:id", async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      if (isNaN(id)) {
        return res.status(400).json({
          message: "Invalid workflow ID"
        });
      }
      
      const workflow = await storage.getWorkflow(id);
      if (!workflow) {
        return res.status(404).json({
          message: "Workflow not found"
        });
      }
      
      return res.json(workflow);
    } catch (error) {
      console.error("[Workflow Fetch Error]", error);
      return res.status(500).json({
        message: error instanceof Error ? error.message : "Unknown error occurred"
      });
    }
  });
  
  app.put("/api/workflows/:id", async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      if (isNaN(id)) {
        return res.status(400).json({
          message: "Invalid workflow ID"
        });
      }
      
      const result = insertWorkflowSchema.partial().safeParse(req.body);
      if (!result.success) {
        return res.status(400).json({
          message: "Invalid workflow data",
          errors: result.error.errors
        });
      }
      
      // Check if workflow exists
      const existing = await storage.getWorkflow(id);
      if (!existing) {
        return res.status(404).json({
          message: "Workflow not found"
        });
      }
      
      // If trying to update the value, check it's not already taken
      if (result.data.value && result.data.value !== existing.value) {
        const valueExists = await storage.getWorkflowByValue(result.data.value);
        if (valueExists && valueExists.id !== id) {
          return res.status(409).json({
            message: "A workflow with this value already exists"
          });
        }
      }
      
      const updated = await storage.updateWorkflow(id, result.data);
      return res.json(updated);
    } catch (error) {
      console.error("[Workflow Update Error]", error);
      return res.status(500).json({
        message: error instanceof Error ? error.message : "Unknown error occurred"
      });
    }
  });
  
  app.delete("/api/workflows/:id", async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      if (isNaN(id)) {
        return res.status(400).json({
          message: "Invalid workflow ID"
        });
      }
      
      const workflow = await storage.getWorkflow(id);
      if (!workflow) {
        return res.status(404).json({
          message: "Workflow not found"
        });
      }
      
      const deleted = await storage.deleteWorkflow(id);
      return res.json({ success: deleted });
    } catch (error) {
      console.error("[Workflow Delete Error]", error);
      return res.status(500).json({
        message: error instanceof Error ? error.message : "Unknown error occurred"
      });
    }
  });
  
  // API endpoint to receive webhook callbacks from RunPod
  app.post("/api/webhook/runpod", async (req, res) => {
    try {
      const { id, status, output, error } = req.body;
      
      if (!id) {
        return res.status(400).json({ 
          message: "Job ID is required" 
        });
      }
      
      console.log(`[Webhook] Received callback for job ${id}, status: ${status}`);
      
      // Check if we already processed this job to avoid duplicates
      if (jobs[id] && jobs[id].status === 'completed') {
        console.log(`[Webhook] Job ${id} already processed, skipping`);
        return res.status(200).json({ success: true });
      }
      
      // Update our local cache
      if (status === 'COMPLETED') {
        let outputImageUrl = null;
        
        if (output?.output_image) {
          // Direct output_image field
          outputImageUrl = output.output_image;
        } else if (output?.images && output.images.length > 0) {
          // Images array format
          outputImageUrl = output.images[0].image || output.images[0];
        } else if (output?.message && output.message.startsWith('data:image/')) {
          // Direct Base64 image in message field
          outputImageUrl = output.message;
        } else if (output?.message) {
          // Base64 encoded image in message field without data URI prefix
          outputImageUrl = `data:image/png;base64,${output.message}`;
        } else if (output?.all_images && output.all_images.length > 0) {
          // RunPod all_images format with path - need to construct a URL to fetch the image
          // For now, we'll try to use the message field which usually contains the Base64 data
          if (output.message) {
            if (output.message.startsWith('data:image/')) {
              outputImageUrl = output.message;
            } else {
              // Assume it's a base64 string
              outputImageUrl = `data:image/png;base64,${output.message}`;
            }
          }
        }
        
        // Save the output image to storage if we have base64 data
        if (outputImageUrl && (outputImageUrl.startsWith('data:image/') || output?.message)) {
          try {
            // Use a timestamp for consistent naming across sync and async - don't use prefixes
            const timestamp = Date.now();
            const outputFilename = `${timestamp}.png`;
            
            // Use the base64 data for storage
            const base64Data = outputImageUrl.startsWith('data:image/') 
              ? outputImageUrl 
              : `data:image/png;base64,${output.message}`;
            
            await saveBase64ImageToStorage(
              base64Data,
              'output_images',
              outputFilename
            );
            console.log(`[Object Storage] Output image saved as ${outputFilename}`);
            
            // Keep the original base64 data for the frontend
            // This ensures the frontend always receives base64 data for consistent handling
          } catch (error) {
            console.error('[Object Storage] Failed to save output image:', error);
            // Continue with the original base64 data if storage fails
          }
        }
        
        jobs[id] = {
          status: 'completed',
          output_image: outputImageUrl,
          timestamp: Date.now()
        };
      } else if (status === 'FAILED') {
        jobs[id] = {
          status: 'failed',
          error: error || 'Unknown error',
          timestamp: Date.now()
        };
      }
      
      return res.status(200).json({ success: true });
    } catch (error) {
      console.error("[Webhook Exception]", error);
      return res.status(500).json({ 
        message: error instanceof Error ? error.message : "Unknown error occurred"
      });
    }
  });
  
  // API proxy endpoint to handle CORS issues and connect to RunPod API
  app.post("/api/process-image", async (req, res) => {
    try {
      const { workflow_name, image, endpointId, waitForResponse } = req.body;
      
      if (!workflow_name || !image || !endpointId) {
        return res.status(400).json({ 
          message: "Workflow name, image, and endpoint ID are required" 
        });
      }

      // Get the API key from environment variables
      const apiKey = process.env.RUNPOD_API_KEY;
      if (!apiKey) {
        return res.status(500).json({
          message: "RunPod API key is not configured"
        });
      }

      // Save input image to object storage with just a timestamp
      const timestamp = Date.now();
      const inputFilename = `${timestamp}.png`;
      
      try {
        await saveBase64ImageToStorage(
          image, 
          'input_images',
          inputFilename
        );
        console.log(`[Object Storage] Input image saved as ${inputFilename}`);
      } catch (error) {
        console.error('[Object Storage] Failed to save input image:', error);
        // Continue processing even if storage fails
      }

      // Determine the correct endpoint URL based on waitForResponse flag
      const endpoint = waitForResponse ? 'runsync' : 'run';
      const apiUrl = `https://api.runpod.ai/v2/${endpointId}/${endpoint}`;
      
      console.log(`[API Request] Forwarding to: ${apiUrl}`);
      console.log(`[API Request] Image data length: ${image.length} characters`);
      console.log(`[API Request] Using endpoint: ${endpointId}`);
      console.log(`[API Request] Using workflow: ${workflow_name}`);
      console.log(`[API Request] Wait for response: ${waitForResponse ? 'Yes' : 'No'}`);
      
      // For async requests, include a webhook URL
      let requestBody: any = {
        input: {
          workflow_name: workflow_name,
          images: [
            {
              name: "uploaded_image.jpg",
              image: image
            }
          ]
        }
      };
      
      // Add webhook URL for asynchronous requests
      if (!waitForResponse) {
        // Determine the base URL for webhooks
        const host = req.headers.host;
        const protocol = req.headers['x-forwarded-proto'] || 'https'; // Default to https for Replit
        const webhookUrl = `${protocol}://${host}/api/webhook/runpod`;
        console.log(`[API Request] Setting webhook URL: ${webhookUrl}`);
        
        // According to the RunPod API, webhook should be a string not an object
        requestBody.webhook = webhookUrl;
      }
      
      // Forward the request to RunPod API with authentication and new format
      const response = await fetch(
        apiUrl, 
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${apiKey}`
          },
          body: JSON.stringify(requestBody)
        }
      );

      let responseText;
      try {
        responseText = await response.text();
        console.log(`[API Response] Raw response: ${responseText.substring(0, 300)}${responseText.length > 300 ? '...' : ''}`);
      } catch (error) {
        console.error('[API Error] Failed to read response text:', error);
        responseText = 'Failed to read response text';
      }
      
      let responseData: any;
      try {
        responseData = JSON.parse(responseText);
        console.log('[API Response] Parsed JSON:', responseData);
      } catch (error) {
        console.error('[API Error] Failed to parse response as JSON:', error);
        responseData = { error: 'Invalid JSON response' };
      }
      
      if (!response.ok) {
        console.error(`[API Error] Status: ${response.status} ${response.statusText}`);
        return res.status(response.status).json({ 
          message: `API Error: ${response.statusText}`,
          details: responseText,
          parsed: responseData
        });
      }

      console.log(`[API Success] Status: ${response.status}`);
      const data = responseData;
      
      // For asynchronous requests, we need to handle the jobId differently
      if (!waitForResponse && data && data.id) {
        console.log(`[API Async] Job ID: ${data.id}`);
        return res.json({
          job_id: data.id,
          status: 'processing',
          message: 'Image processing started asynchronously'
        });
      }
      
      // For synchronous requests, save the output image and return the data
      if (waitForResponse && data && data.status === 'COMPLETED') {
        // Generate a unique job ID for sync requests if not present - just use timestamp
        const jobId = data.id || `${Date.now()}`;
        
        // Extract output image URL from various response formats
        let outputImageUrl = null;
            
        if (data.output?.output_image) {
          // Direct output_image field
          outputImageUrl = data.output.output_image;
        } else if (data.output?.images && data.output.images.length > 0) {
          // Images array format
          outputImageUrl = data.output.images[0].image || data.output.images[0];
        } else if (data.output?.message && data.output.message.startsWith('data:image/')) {
          // Direct Base64 image in message field
          outputImageUrl = data.output.message;
        } else if (data.output?.message) {
          // Base64 encoded image in message field without data URI prefix
          outputImageUrl = `data:image/png;base64,${data.output.message}`;
        } else if (data.output?.all_images && data.output.all_images.length > 0) {
          // RunPod all_images format
          if (data.output.message) {
            if (data.output.message.startsWith('data:image/')) {
              outputImageUrl = data.output.message;
            } else {
              // Assume it's a base64 string
              outputImageUrl = `data:image/png;base64,${data.output.message}`;
            }
          }
        }
        
        // Save the output image to storage if we have base64 data
        if (outputImageUrl && (outputImageUrl.startsWith('data:image/') || data.output?.message)) {
          try {
            // Use a timestamp for consistent naming across sync and async - don't use prefixes
            const timestamp = Date.now();
            const outputFilename = `${timestamp}.png`;
            
            // Use the base64 data for storage
            const base64Data = outputImageUrl.startsWith('data:image/') 
              ? outputImageUrl 
              : `data:image/png;base64,${data.output.message}`;
            
            await saveBase64ImageToStorage(
              base64Data,
              'output_images',
              outputFilename
            );
            console.log(`[Object Storage] Output image saved as ${outputFilename}`);
            
            // Keep the base64 data for the frontend - don't add a URL to the response
            // This ensures the frontend always receives base64 data for consistent handling
          } catch (error) {
            console.error('[Object Storage] Failed to save output image:', error);
            // Continue with the original base64 data if storage fails
          }
        }
      }
      
      // Return the complete data (possibly enhanced with our stored image URL)
      return res.json(data);
    } catch (error) {
      console.error("[API Exception]", error);
      return res.status(500).json({ 
        message: error instanceof Error ? error.message : "Unknown error occurred"
      });
    }
  });

  const httpServer = createServer(app);
  return httpServer;
}
