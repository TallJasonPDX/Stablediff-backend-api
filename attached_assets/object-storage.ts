import { Client } from '@replit/object-storage';
import { Buffer } from 'buffer';

// Create reusable client
const storage = new Client();

// Helper function to save base64 image to object storage
export async function saveBase64ImageToStorage(
  base64Data: string, 
  folder: string, 
  filename: string
): Promise<string> {
  try {
    // Remove the data:image/png;base64, part if it exists
    const base64Image = base64Data.replace(/^data:image\/(png|jpeg|jpg|gif);base64,/, '');
    
    // Convert base64 to buffer
    const imageBuffer = Buffer.from(base64Image, 'base64');
    
    // Create the full path
    const objectKey = `${folder}/${filename}`;
    
    // Store the file in object storage
    const result = await storage.uploadFromBytes(objectKey, imageBuffer);
    
    if (result.error) {
      throw new Error(`Failed to upload image: ${result.error.message}`);
    }
    
    console.log(`[Object Storage] Saved image to ${objectKey}`);
    
    return objectKey;
  } catch (error) {
    console.error('[Object Storage] Error saving image:', error);
    throw error;
  }
}

// Helper function to check if an object exists
export async function objectExists(folder: string, filename: string): Promise<boolean> {
  try {
    const objectKey = `${folder}/${filename}`;
    const result = await storage.exists(objectKey);
    
    if (result.error) {
      console.error(`[Object Storage] Error checking if ${objectKey} exists:`, result.error);
      return false;
    }
    
    return result.value;
  } catch (error) {
    console.error(`[Object Storage] Exception checking if ${folder}/${filename} exists:`, error);
    return false;
  }
}

// Helper function to get object's URL
// Simply returns the relative path to the object which will be served by Replit
export async function getObjectUrl(folder: string, filename: string): Promise<string> {
  try {
    const objectKey = `${folder}/${filename}`;
    
    // First check if the object exists
    const result = await storage.exists(objectKey);
    if (result.error || !result.value) {
      console.error(`[Object Storage] Object ${objectKey} does not exist or there was an error`);
      return '';
    }
    
    // Simply return the relative path, which will be resolved by the frontend
    // For Replit, this works because storage objects can be accessed via their path
    const url = `/${objectKey}`;
    
    console.log(`[Object Storage] Generated URL for ${objectKey}: ${url}`);
    return url;
  } catch (error) {
    console.error('[Object Storage] Error getting object URL:', error);
    return '';
  }
}