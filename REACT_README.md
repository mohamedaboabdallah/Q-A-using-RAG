# RAG System Frontend

A modern React frontend for your RAG (Retrieval-Augmented Generation) system that connects to your Flask backend.

## Features

- **🔐 Login Page**: Secure authentication with form validation
- **📁 Upload Page**: Drag-and-drop file upload with progress tracking
- **💬 Chatbot Page**: Real-time chat interface connected to your Flask backend
- **🎨 Modern UI**: Beautiful, responsive design with animations
- **📱 Mobile Friendly**: Fully responsive across all devices

## Project Structure

```
src/
├── components/
│   ├── Login.js          # Login page component
│   ├── Login.css         # Login page styles
│   ├── Upload.js         # File upload component
│   ├── Upload.css        # Upload page styles
│   ├── Chatbot.js        # Chat interface component
│   └── Chatbot.css       # Chatbot page styles
├── App.js                # Main app with routing
├── App.css               # App-level styles
├── index.js              # React entry point
└── index.css             # Global styles
```

## Installation & Setup

1. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

2. **Start your Flask backend first:**
   ```bash
   python server.py
   ```
   Make sure your Flask server is running on `http://localhost:5000`

3. **Start the React development server:**
   ```bash
   npm start
   ```
   The React app will open at `http://localhost:3000`

## How to Use

### 1. Login Page (`/`)
- Enter any username and password (minimum 6 characters)
- The demo accepts any valid credentials for testing
- Successfully logs you into the upload page

### 2. Upload Page (`/upload`)
- Upload PDF, TXT, DOC, or DOCX files (max 10MB each)
- Drag and drop or click to select files
- View upload progress and file validation
- Automatically redirects to chat after successful upload

### 3. Chatbot Page (`/chat`)
- Chat interface connected to your Flask `/chat` endpoint
- Real-time messaging with typing indicators
- Message history with timestamps
- Error handling for connection issues

## Integration with Flask Backend

The React app is configured to work with your existing Flask `server.py`:

- **Proxy Configuration**: Requests to `/chat` are automatically proxied to `http://localhost:5000`
- **API Endpoint**: The chatbot sends POST requests to `/chat` with the message payload
- **Expected Response**: Your Flask backend should return `{"reply": "response_text"}`

### Current Flask Integration

Your `server.py` already has the `/chat` endpoint that the React app uses:

```python
@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json['message']
    reply = llm_response(user_message)
    return jsonify({'reply': reply})
```

## Customization

### Adding File Upload to Flask

To add file upload functionality to your Flask backend, you can add this route:

```python
@app.route('/upload', methods=['POST'])
def upload_files():
    files = request.files.getlist('files')
    for file in files:
        if file and file.filename:
            # Process and store your files here
            # Add to your RAG system's document store
            pass
    return jsonify({'status': 'success', 'message': 'Files uploaded successfully'})
```

### Styling Customization

- **Colors**: Modify the gradient colors in `src/index.css`
- **Components**: Each component has its own CSS file for easy customization
- **Responsive**: All components are mobile-responsive

## Authentication

The current authentication is demo-only using localStorage:
- For production, implement proper JWT tokens
- Add backend authentication endpoints
- Replace localStorage with secure token management

## Available Scripts

- `npm start` - Start development server
- `npm build` - Build for production
- `npm test` - Run tests
- `npm run eject` - Eject from Create React App (not recommended)

## Browser Support

- Chrome (recommended)
- Firefox
- Safari
- Edge

## Troubleshooting

### Common Issues

1. **"Cannot connect to server"**
   - Make sure Flask backend is running on port 5000
   - Check if CORS is properly configured

2. **"Module not found"**
   - Run `npm install` to install dependencies
   - Clear node_modules and reinstall if needed

3. **Upload not working**
   - Ensure files are under 10MB
   - Check supported file types (PDF, TXT, DOC, DOCX)

### Development Tips

- Use browser developer tools to debug API calls
- Check the Network tab for backend communication
- Console logs are available for debugging

## Next Steps

1. **Connect Upload**: Implement actual file upload to your Flask backend
2. **Add Authentication**: Implement proper user authentication
3. **Enhance Chat**: Add features like chat history, file references
4. **Deploy**: Build for production and deploy to your preferred platform

## Support

The app is configured to work seamlessly with your existing Flask RAG system. The chatbot will communicate with your `llm_response` function through the `/chat` endpoint.

Happy coding! 🚀