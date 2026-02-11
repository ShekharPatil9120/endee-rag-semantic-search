// Chat state
let isLoading = false;
let messageCount = 0;

// DOM elements
const chatMessages = document.getElementById('chatMessages');
const questionInput = document.getElementById('questionInput');
const askButton = document.getElementById('askButton');

// Initialize: clear empty state and set up event listeners
document.addEventListener('DOMContentLoaded', function() {
    askButton.addEventListener('click', sendQuestion);
    questionInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !isLoading) {
            sendQuestion();
        }
    });
});

/**
 * Add a message to the chat display
 * @param {string} text - Message text
 * @param {string} role - 'user' or 'assistant' or 'error'
 * @param {object} meta - Optional metadata (sources_used, etc.)
 */
function addMessage(text, role = 'assistant', meta = null) {
    // Remove empty state if first message
    if (messageCount === 0) {
        chatMessages.innerHTML = '';
    }
    messageCount++;

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    let content = text;
    if (meta && meta.sources_used) {
        content += `<div class="message-meta">Sources: ${meta.sources_used}</div>`;
    }
    
    messageDiv.innerHTML = content;
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Show loading indicator (typing animation)
 */
function showLoadingIndicator() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message loading';
    messageDiv.id = 'loadingIndicator';
    messageDiv.innerHTML = `
        <div class="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
        </div>
        <div style="margin-top: 8px; font-size: 12px;">Thinking...</div>
    `;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Remove loading indicator
 */
function removeLoadingIndicator() {
    const loadingDiv = document.getElementById('loadingIndicator');
    if (loadingDiv) {
        loadingDiv.remove();
    }
}

/**
 * Send question to RAG chatbot
 */
async function sendQuestion() {
    const question = questionInput.value.trim();

    // Validate
    if (!question) {
        addMessage('Please enter a question.', 'error');
        return;
    }

    if (isLoading) {
        return; // Prevent duplicate requests
    }

    // Clear input and show user message
    questionInput.value = '';
    addMessage(question, 'user');

    // Show loading indicator
    isLoading = true;
    askButton.disabled = true;
    showLoadingIndicator();

    try {
        // Build query URL
        const encodedQuestion = encodeURIComponent(question);
        const url = `/chat/ragbot/?q=${encodedQuestion}`;

        // Fetch answer from backend
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        // Remove loading indicator
        removeLoadingIndicator();

        // Handle response
        if (!response.ok) {
            const errorData = await response.json();
            const errorMessage = errorData.reply || errorData.error || 'An error occurred.';
            addMessage(errorMessage, 'error');
            return;
        }

        const data = await response.json();

        // Display assistant's reply
        const meta = {
            sources_used: data.sources_used || 0
        };
        addMessage(data.reply, 'assistant', meta);

    } catch (error) {
        removeLoadingIndicator();
        console.error('Error:', error);
        addMessage(
            `Network error: ${error.message}. Please check your connection and try again.`,
            'error'
        );
    } finally {
        isLoading = false;
        askButton.disabled = false;
        questionInput.focus();
    }
}

/**
 * Clear chat history
 */
function clearChat() {
    chatMessages.innerHTML = `
        <div class="empty-state">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <p>Start by asking a question about smart farming!</p>
        </div>
    `;
    messageCount = 0;
    questionInput.focus();
}
