// DOM Elements
const fileInput = document.getElementById('file-input');
const fileName = document.getElementById('file-name');
const inputText = document.getElementById('input-text');
const outputText = document.getElementById('output-text');
const transformBtn = document.getElementById('transform-btn');
const copyBtn = document.getElementById('copy-btn');
const downloadBtn = document.getElementById('download-btn');
const downloadFormat = document.getElementById('download-format');
const loginBtn = document.getElementById('login-btn');
const loginModal = document.getElementById('login-modal');
const closeButtons = document.querySelectorAll('.close');

// Gemini API configuration (loaded from config)
let API_KEY, API_URL;

// Initialize configuration
function initConfig() {
    // In a production app, these would come from MrWlahConfig
    // For this demo, we'll use placeholders
    API_KEY = window.MrWlahConfig?.gemini?.apiKey || 'YOUR_GEMINI_API_KEY';
    API_URL = window.MrWlahConfig?.gemini?.apiUrl || 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent';
}

// Initialize app
function init() {
    initConfig();
    // Add preserve font option
    addPreserveFontCheckbox();
}

// Add preserve font checkbox to the UI
function addPreserveFontCheckbox() {
    const controlPanel = document.querySelector('.control-panel');
    
    // Create the preserve font option
    const preserveFontDiv = document.createElement('div');
    preserveFontDiv.className = 'preserve-font';
    preserveFontDiv.innerHTML = `
        <label for="preserve-font">
            <input type="checkbox" id="preserve-font" checked>
            Preserve Font Style
        </label>
    `;
    
    // Add it to the control panel
    controlPanel.appendChild(preserveFontDiv);
    
    // Add styles
    const style = document.createElement('style');
    style.textContent = `
        .preserve-font {
            margin-top: 10px;
            display: flex;
            align-items: center;
        }
        .preserve-font label {
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 5px;
        }
        .preserve-font input {
            cursor: pointer;
        }
    `;
    document.head.appendChild(style);
}

// File Upload Handling
fileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    fileName.textContent = file.name;
    
    try {
        let text;
        
        if (file.type === 'text/plain') {
            text = await file.text();
        } 
        else if (file.type === 'application/pdf') {
            // In a real implementation, you would use a PDF parsing library
            alert('PDF support would be implemented with a PDF parsing library');
            return;
        }
        else if (file.type.includes('word')) {
            // In a real implementation, you would use a DOCX parsing library
            alert('DOCX support would be implemented with a document parsing library');
            return;
        }
        
        inputText.value = text || '';
    } catch (error) {
        console.error('Error reading file:', error);
        alert('Error reading file. Please try again.');
    }
});

// Text Transformation with Gemini API
transformBtn.addEventListener('click', async () => {
    const text = inputText.value.trim();
    const tone = document.getElementById('tone').value;
    const preserveFont = document.getElementById('preserve-font')?.checked || true;
    
    if (!text) {
        alert('Please enter or upload some text to transform.');
        return;
    }
    
    // Show loading state
    transformBtn.disabled = true;
    transformBtn.textContent = 'Transforming...';
    outputText.textContent = 'Applying humanizing transformations...';
    
    try {
        const transformedText = await transformTextWithGemini(text, tone, preserveFont);
        
        // If transformed text has HTML content, use innerHTML, otherwise use textContent
        if (/<[a-z][\s\S]*>/i.test(transformedText)) {
            outputText.innerHTML = transformedText;
        } else {
            outputText.textContent = transformedText;
        }
    } catch (error) {
        console.error('Error transforming text:', error);
        outputText.textContent = 'Error: Failed to transform text. Please try again.';
    } finally {
        transformBtn.disabled = false;
        transformBtn.textContent = 'Transform Text';
    }
});

// Gemini API Call
async function transformTextWithGemini(text, tone, preserveFont = true) {
    // In a real implementation with a backend server, we would call the API endpoint
    try {
        const response = await fetch('/api/transform', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                text,
                tone,
                preserveFont
            })
        });
        
        if (!response.ok) {
            throw new Error('API request failed');
        }
        
        const data = await response.json();
        return data.transformedText;
    } catch (error) {
        console.error('API error:', error);
        
        // Fallback to simulation if server is not available
        console.log('Falling back to simulated transformation');
        return simulateTransformation(text, tone);
    }
}

// Simulate transformation (for demo when backend is unavailable)
async function simulateTransformation(text, tone) {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Simulated transformations based on tone
    const toneTransformations = {
        casual: "Hey, I've been thinking about this quite a bit lately. You know how it goes, right? Sometimes you just can't help but wonder...",
        professional: "Having considered the matter extensively, it's worth noting the significant implications. In my professional experience...",
        scientific: "Upon analysis of the available data, several patterns emerge. From my laboratory observations over the past decade...",
        educational: "Let me explain this concept in a way that connects to real-world scenarios. When I was teaching this material...",
        engaging: "Isn't it fascinating how this works? I remember when I first discovered this - it completely changed my perspective!",
        humorous: "So there I was, utterly confused about this whole thing. Classic me, right? Let me tell you about the time I...",
        storytelling: "The journey began on an ordinary Tuesday. Little did I know that this simple question would lead me down a path of discovery..."
    };
    
    const intro = toneTransformations[tone] || toneTransformations.casual;
    return intro + " " + text.replace(/\.\s+/g, ".\n\n"); // Add paragraph breaks for readability
}

// Copy to Clipboard
copyBtn.addEventListener('click', () => {
    // If output contains HTML, we need to get its inner text or HTML
    const isHTML = outputText.innerHTML !== outputText.textContent;
    const text = isHTML ? outputText.innerHTML : outputText.textContent;
    
    if (!text) {
        alert('No text to copy.');
        return;
    }
    
    // Use clipboard API for plain text or create a temporary element for HTML
    if (isHTML) {
        // Create a textarea to hold the HTML content
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        
        copyBtn.textContent = 'Copied!';
        setTimeout(() => {
            copyBtn.textContent = 'Copy';
        }, 2000);
    } else {
        navigator.clipboard.writeText(text)
            .then(() => {
                copyBtn.textContent = 'Copied!';
                setTimeout(() => {
                    copyBtn.textContent = 'Copy';
                }, 2000);
            })
            .catch(err => {
                console.error('Failed to copy text:', err);
                alert('Failed to copy text. Please try again.');
            });
    }
});

// Download Text
downloadBtn.addEventListener('click', () => {
    // If output contains HTML, we need to get its inner text or HTML
    const isHTML = outputText.innerHTML !== outputText.textContent;
    const text = isHTML ? outputText.innerHTML : outputText.textContent;
    const format = downloadFormat.value;
    
    if (!text) {
        alert('No text to download.');
        return;
    }
    
    // In a real implementation, PDF and DOC would use proper libraries
    if (format === 'pdf' || format === 'doc') {
        alert(`In production, this would generate a proper ${format.toUpperCase()} file.`);
        return;
    }
    
    // Determine content type based on format and content
    let contentType = 'text/plain';
    let fileName = `mr-wlah-transformed.${format}`;
    let content = text;
    
    // If HTML content and downloading as txt, consider if we should save as HTML
    if (isHTML && format === 'txt' && confirm('Your text contains formatting. Save as HTML instead?')) {
        contentType = 'text/html';
        fileName = 'mr-wlah-transformed.html';
        content = `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Mr. Wlah Transformed Text</title>
</head>
<body>
    ${content}
</body>
</html>`;
    }
    
    // Create and download the file
    const blob = new Blob([content], { type: contentType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
});

// Modal Handling
loginBtn.addEventListener('click', () => {
    loginModal.style.display = 'block';
});

closeButtons.forEach(button => {
    button.addEventListener('click', () => {
        loginModal.style.display = 'none';
    });
});

window.addEventListener('click', (e) => {
    if (e.target === loginModal) {
        loginModal.style.display = 'none';
    }
});

// Pixel Writing Effect
function pixelWriteEffect(element, text, index = 0, speed = 30) {
    if (index < text.length) {
        element.textContent += text.charAt(index);
        setTimeout(() => pixelWriteEffect(element, text, index + 1, speed), speed);
    }
}

// Initialize when the DOM is loaded
document.addEventListener('DOMContentLoaded', init); 