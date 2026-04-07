---
name: whatsapp-image-send
description: Send images, videos, audio, or documents via WhatsApp by downloading, copying to workspace, sending, and cleaning up temporary files.
---

# WhatsApp Image Send

## Workflow

1. **Download**: Save file to `/tmp/<filename>`
   ```bash
   curl -o /tmp/<filename> <url>
   ```

2. **Copy to workspace**: WhatsApp requires workspace path
   ```bash
   cp /tmp/<filename> ~/.openclaw/workspace/
   ```

3. **Send to WhatsApp**
   ```bash
   message --channel whatsapp --target <phone> --filePath ~/.openclaw/workspace/<filename> --message "<caption>"
   ```

4. **Cleanup**: Delete temp file
   ```bash
   rm /tmp/<filename>
   ```

## Notes

- Phone format: +country + number (e.g., +14843124960)
- Supported: jpg, png, gif, video, audio, document
