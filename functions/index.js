const { onObjectFinalized } = require("firebase-functions/v2/storage");
const { initializeApp } = require("firebase-admin/app");
const { getStorage } = require("firebase-admin/storage");
const sharp = require("sharp");
const path = require("path");
const os = require("os");
const fs = require("fs");

// Initialize Firebase Admin SDK
initializeApp();

exports.processImage = onObjectFinalized(
  {
    bucket: 'urqrs-baf30.firebasestorage.app', // Replace with your actual bucket name
    region: 'asia-south1'              // Replace with your bucket's region if different
  },
  async function (event) {
        const object = event.data;

        // Exit if the file is not an image.
        if (!object.contentType || !object.contentType.startsWith("image/")) {
            console.log("This file is not an image.");
            return null;
        }

        // Only process images uploaded to the 'uploads/original/' folder.
        const filePath = object.name;
        if (!filePath.startsWith("uploads/original/")) {
            console.log("Image not in 'uploads/original/' folder. Skipping processing.");
            return null;
        }

        const bucket = getStorage().bucket(object.bucket);
        const fileName = path.basename(filePath);
        const tempFilePath = path.join(os.tmpdir(), fileName);

        // Download the image from Firebase Storage.
        await bucket.file(filePath).download({ destination: tempFilePath });
        console.log("Image downloaded locally to", tempFilePath);

        // Process the image without resizing (re-encode only).
        const processedFileName = "processed_" + fileName;
        const tempProcessedFilePath = path.join(os.tmpdir(), processedFileName);
        await sharp(tempFilePath).toFile(tempProcessedFilePath);
        console.log("Image processed (no resizing) and saved locally to", tempProcessedFilePath);

        // Upload the processed image back to Firebase Storage.
        const destination = path.join("uploads/processed/", processedFileName);
        await bucket.upload(tempProcessedFilePath, { destination });
        console.log("Processed image uploaded to", destination);

        // Clean up temporary files.
        fs.unlinkSync(tempFilePath);
        fs.unlinkSync(tempProcessedFilePath);

        return null;
    }
);
