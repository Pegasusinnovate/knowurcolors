const functions = require('firebase-functions');
const admin = require('firebase-admin');
const os = require('os');
const path = require('path');
const fs = require('fs');

admin.initializeApp();
const bucket = admin.storage().bucket();

exports.processImageOnUpload = functions.storage.object().onFinalize(async (object) => {
  try {
    const filePath = object.name;
    const contentType = object.contentType;
    // Only process image files.
    if (!contentType || !contentType.startsWith('image/')) {
      console.log('Not an image, skipping processing.');
      return null;
    }
    
    console.log(`Processing file: ${filePath}`);
    // Process only files in "uploads/" folder.
    if (!filePath.startsWith('uploads/')) {
      console.log('File not in uploads/ folder, skipping.');
      return null;
    }
    
    // Define destination path for the processed file.
    const fileName = path.basename(filePath);
    const processedPath = `processed/result_${fileName}`;
    
    // Create temporary local paths.
    const tempFilePath = path.join(os.tmpdir(), fileName);
    const tempProcessedPath = path.join(os.tmpdir(), `result_${fileName}`);
    
    // Download the file from Firebase Storage.
    await bucket.file(filePath).download({ destination: tempFilePath });
    console.log('Downloaded file locally to', tempFilePath);
    
    // ----- PROCESSING STEP -----
    // For demonstration, simply copy the file.
    // Replace this block with your actual image processing logic.
    fs.copyFileSync(tempFilePath, tempProcessedPath);
    console.log('Processed image saved locally as', tempProcessedPath);
    
    // Upload the processed image to Firebase Storage.
    await bucket.upload(tempProcessedPath, {
      destination: processedPath,
      metadata: { contentType: contentType },
    });
    console.log('Uploaded processed image to', processedPath);
    
    // Clean up temporary files.
    fs.unlinkSync(tempFilePath);
    fs.unlinkSync(tempProcessedPath);
    
    return null;
  } catch (error) {
    console.error('Error processing image:', error);
    return null;
  }
});
