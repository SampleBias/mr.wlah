// DOM Elements
const fileInput = document.getElementById('file-input');
const fileName = document.getElementById('file-name');
const removeFileBtn = document.getElementById('remove-file-btn');
const inputText = document.getElementById('input-text');
const outputText = document.getElementById('output-text');
const transformBtn = document.getElementById('transform-btn');
const copyBtn = document.getElementById('copy-btn');
const downloadBtn = document.getElementById('download-btn');
const downloadFormat = document.getElementById('download-format');
const loginBtn = document.getElementById('login-btn');
const loginModal = document.getElementById('login-modal');
const closeButtons = document.querySelectorAll('.close');
const clearInputBtn = document.getElementById('clear-input-btn');
const clearOutputBtn = document.getElementById('clear-output-btn');
const docProcessingContainer = document.getElementById('doc-processing-container');
const docProcessingProgress = document.querySelector('.doc-processing-progress');
const docProcessingPercentage = document.querySelector('.doc-processing-percentage');

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
    // Show the remove file button
    removeFileBtn.style.display = 'inline-block';
    
    try {
        let text;
        
        if (file.type === 'text/plain') {
            text = await file.text();
            inputText.value = text || '';
        } 
        else if (file.type === 'application/pdf') {
            // Process PDF document with our agent
            await processPDFDocument(file);
        }
        else if (file.type.includes('word')) {
            // Process Word document with our agent
            await processWordDocument(file);
        } else {
            alert('Unsupported file format. Please upload a .txt, .doc, .docx, or .pdf file.');
        }
    } catch (error) {
        console.error('Error reading file:', error);
        alert('Error reading file. Please try again.');
    }
});

// PDF Document Processing Agent
async function processPDFDocument(file) {
    try {
        // Show processing container
        docProcessingContainer.classList.add('active');
        docProcessingProgress.style.width = '0%';
        docProcessingPercentage.textContent = '0%';
        
        // Set the document type class for proper icon display
        const processingLabel = document.querySelector('.doc-processing-label');
        processingLabel.classList.remove('docx');
        processingLabel.classList.add('pdf');
        
        // Start processing animation
        const totalSteps = 5;
        
        // Step 1: Initialize
        await updateProgress(1, totalSteps, 'Initializing PDF processing...');
        
        // Step 2: Reading file
        await updateProgress(2, totalSteps, 'Reading PDF structure...');
        
        // Step 3: Extracting text
        await updateProgress(3, totalSteps, 'Extracting PDF content...');
        
        // Step 4: Processing layout
        await updateProgress(4, totalSteps, 'Analyzing PDF layout...');
        
        // Step 5: Finalizing
        await updateProgress(5, totalSteps, 'Finalizing PDF extraction...');
        
        // Process the document on the server
        const result = await processFileOnServer(file);
        
        // Complete
        docProcessingProgress.style.width = '100%';
        docProcessingPercentage.textContent = '100%';
        
        // Hide processing container after a short delay
        setTimeout(() => {
            docProcessingContainer.classList.remove('active');
        }, 500);
        
        return result;
    } catch (error) {
        // Handle error gracefully
        handleDocProcessingError(error.message || 'Error processing PDF');
        throw error;
    }
}

// Word Document Processing Agent
async function processWordDocument(file) {
    try {
        // Show processing container
        docProcessingContainer.classList.add('active');
        docProcessingProgress.style.width = '0%';
        docProcessingPercentage.textContent = '0%';
        
        // Set the document type class for proper icon display
        const processingLabel = document.querySelector('.doc-processing-label');
        processingLabel.classList.remove('pdf');
        processingLabel.classList.add('docx');
        
        // Start processing animation
        const totalSteps = 5;
        
        // Step 1: Initialize
        await updateProgress(1, totalSteps, 'Initializing document processing...');
        
        // Step 2: Reading file
        await updateProgress(2, totalSteps, 'Reading document structure...');
        
        // Step 3: Extracting text
        await updateProgress(3, totalSteps, 'Extracting document content...');
        
        // Step 4: Processing formatting
        await updateProgress(4, totalSteps, 'Processing document formatting...');
        
        // Step 5: Finalizing
        await updateProgress(5, totalSteps, 'Finalizing document extraction...');
        
        // Process the document on the server
        const result = await processFileOnServer(file);
        
        // Complete
        docProcessingProgress.style.width = '100%';
        docProcessingPercentage.textContent = '100%';
        
        // Hide processing container after a short delay
        setTimeout(() => {
            docProcessingContainer.classList.remove('active');
        }, 500);
        
        return result;
    } catch (error) {
        // Handle error gracefully
        handleDocProcessingError(error.message || 'Error processing document');
        throw error;
    }
}

// Handle document processing errors
function handleDocProcessingError(errorMessage) {
    // Show error in processing container
    docProcessingContainer.classList.add('active');
    const processingLabel = document.querySelector('.doc-processing-label');
    processingLabel.textContent = 'Error Processing Document';
    processingLabel.style.color = 'var(--secondary-color)';
    
    // Remove specific document type classes
    processingLabel.classList.remove('pdf', 'docx');
    
    docProcessingPercentage.textContent = 'Failed';
    docProcessingPercentage.style.color = 'var(--secondary-color)';
    docProcessingProgress.style.width = '100%';
    docProcessingProgress.style.backgroundColor = 'var(--secondary-color)';
    
    // Log the error
    console.error('Document processing error:', errorMessage);
    
    // Hide error after a delay
    setTimeout(() => {
        // Reset styles
        processingLabel.style.color = '';
        processingLabel.textContent = 'Processing Document';
        docProcessingPercentage.style.color = '';
        docProcessingProgress.style.backgroundColor = '';
        
        // Hide container
        docProcessingContainer.classList.remove('active');
    }, 3000);
}

// Update progress bar
async function updateProgress(step, totalSteps, message) {
    return new Promise(resolve => {
        const percentage = Math.floor((step / totalSteps) * 100);
        
        // Update progress bar and percentage
        docProcessingProgress.style.width = `${percentage}%`;
        docProcessingPercentage.textContent = `${percentage}%`;
        
        // Update processing label
        document.querySelector('.doc-processing-label').textContent = message;
        
        // Simulate processing time
        setTimeout(resolve, 600);
    });
}

// Process file on server
async function processFileOnServer(file) {
    // Create a FormData object to send the file
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/api/transform', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Server processing failed');
        }
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Update input text with extracted content
        inputText.value = data.originalText || '';
        
        return data.originalText;
    } catch (error) {
        console.error('Error processing file on server:', error);
        alert('Error processing document. Please try again or use a different file.');
        throw error;
    }
}

// Remove File Handling
removeFileBtn.addEventListener('click', () => {
    // Clear the file input
    fileInput.value = '';
    // Reset the file name display
    fileName.textContent = 'No file selected';
    // Hide the remove button
    removeFileBtn.style.display = 'none';
    // Hide the document processing container
    docProcessingContainer.classList.remove('active');
    // Clear the input text area if it contains file content
    if (inputText.value && confirm('Do you want to clear the text that was loaded from the file?')) {
        inputText.value = '';
        inputText.focus();
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
    
    // Calculate original word count
    const originalWordCount = text.split(/\s+/).filter(word => word.length > 0).length;
    
    // Show loading state
    transformBtn.disabled = true;
    transformBtn.textContent = 'Transforming...';
    outputText.textContent = 'Applying humanizing transformations...';
    
    try {
        const transformedText = await transformTextWithGemini(text, tone, preserveFont, originalWordCount);
        
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
async function transformTextWithGemini(text, tone, preserveFont = true, targetWordCount = null) {
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
                preserveFont,
                targetWordCount
            })
        });
        
        if (!response.ok) {
            throw new Error('API request failed');
        }
        
        const data = await response.json();
        
        // Clean the response on the client side as well, just in case
        let transformedText = data.transformedText;
        transformedText = cleanLLMResponse(transformedText);
        
        // Check if we need to adjust word count
        if (targetWordCount) {
            return ensureWordCount(transformedText, targetWordCount);
        }
        
        return transformedText;
    } catch (error) {
        console.error('API error:', error);
        
        // Fallback to simulation if server is not available
        console.log('Falling back to simulated transformation');
        const simulated = simulateTransformation(text, tone);
        
        // Check if we need to adjust word count
        if (targetWordCount) {
            return ensureWordCount(simulated, targetWordCount);
        }
        
        return simulated;
    }
}

// Clean LLM response to remove meta-text
function cleanLLMResponse(text) {
    // Common patterns for LLM meta-text
    const prefacePatterns = [
        /^(Here'?s|Here is|I'?ve|I have|Below is|The following is).*?:\s*\n+/i,
        /^(Sure|Okay|Alright|Of course|I'd be happy to|I can|I will).*?:\s*\n+/i,
        /^(I'?ve transformed|I'?ve rewritten|I'?ve humanized|I'?ve modified).*?:\s*\n+/i,
        /^(Your text|The text|This content) (has been|is now).*?:\s*\n+/i,
        /^(In|With|Using|Employing|Applying) a.*?tone.*?:\s*\n+/i,
        /^(Transformed version|Human version|Human-like version|Rewritten version).*?:\s*\n+/i,
    ];
    
    const concludingPatterns = [
        /\n+\s*(I hope|Hope|Hopefully) (this|that|these|it).*?\.$/i,
        /\n+\s*(Let me know|Feel free to|Please) (if|to|contact).*?\.$/i,
        /\n+\s*(This|The text|This version|This rewrite) (should|now|has).*?\.$/i,
        /\n+\s*(Is there|Do you|Would you|If you) (anything|like|need).*?\.$/i,
        /\n+\s*(Thank you|Thanks) (for|and).*?\.$/i,
    ];
    
    // Remove preface patterns
    for (const pattern of prefacePatterns) {
        text = text.replace(pattern, '');
    }
    
    // Remove concluding patterns
    for (const pattern of concludingPatterns) {
        text = text.replace(pattern, '');
    }
    
    // Remove any lingering whitespace
    return text.trim();
}

// Function to ensure word count is within tolerance of target
function ensureWordCount(text, targetWordCount, tolerance = 100) {
    const words = text.split(/\s+/).filter(word => word.length > 0);
    const currentWordCount = words.length;
    
    // If already within tolerance, return as is
    if (Math.abs(currentWordCount - targetWordCount) <= tolerance) {
        return text;
    }
    
    if (currentWordCount > targetWordCount + tolerance) {
        // Text is too long, truncate
        const truncatedWords = words.slice(0, targetWordCount + tolerance);
        // Add an ellipsis to the last sentence
        let result = truncatedWords.join(' ');
        // Make sure we end with proper punctuation
        if (!result.endsWith('.') && !result.endsWith('!') && !result.endsWith('?')) {
            result += '.';
        }
        return result;
    } else if (currentWordCount < targetWordCount - tolerance) {
        // Text is too short, pad with filler
        const fillersPerTone = {
            casual: [
                "I might be missing something here, but that's my take on it.",
                "I've been thinking about this quite a bit lately.",
                "There's probably more to say, but those are my thoughts for now.",
                "I hope that makes sense to you too.",
                "Let me know if you want me to elaborate on any of this."
            ],
            professional: [
                "Additional considerations may apply depending on specific contexts.",
                "Further analysis could provide more detailed insights.",
                "These observations are based on available information and professional judgment.",
                "I'd be happy to discuss any aspects of this in more detail if needed.",
                "This analysis represents current understanding and may evolve with new information."
            ],
            scientific: [
                "Further research would be beneficial to validate these preliminary findings.",
                "The limitations of current methodologies should be acknowledged.",
                "Statistical significance would need to be established through controlled studies.",
                "These observations align with existing literature in the field.",
                "Peer review would be necessary to confirm these interpretations."
            ],
            educational: [
                "This concept connects to several other important principles worth exploring.",
                "Students often find practical applications helpful for reinforcing these ideas.",
                "Consider how these concepts build on previously established knowledge.",
                "Various learning approaches might be useful for different aspects of this topic.",
                "Reflection questions can help deepen understanding of these principles."
            ]
        };
        
        // Get fillers for specified tone or use casual as default
        const fillers = fillersPerTone[tone] || fillersPerTone.casual;
        
        // Calculate how many fillers we need
        const wordsToAdd = targetWordCount - tolerance - currentWordCount;
        let fillerWords = 0;
        let result = text;
        
        // Add fillers until we reach the target range
        while (fillerWords < wordsToAdd) {
            const randomFiller = fillers[Math.floor(Math.random() * fillers.length)];
            result += " " + randomFiller;
            fillerWords += randomFiller.split(/\s+/).length;
        }
        
        return result;
    }
    
    return text;
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

// Clear input text
clearInputBtn.addEventListener('click', () => {
    inputText.value = '';
    inputText.focus();
});

// Clear output text
clearOutputBtn.addEventListener('click', () => {
    outputText.textContent = '';
});

// Initialize when the DOM is loaded
document.addEventListener('DOMContentLoaded', init); 