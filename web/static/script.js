document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    // System information elements  
    const modelInfoElement = document.getElementById('model-info');  
    const warningMessage = document.getElementById('warning-message');  
    
    // Query related elements  
    const queryInput = document.getElementById('query-input');  
    const queryBtn = document.getElementById('query-btn');  
    const queryLoading = document.getElementById('query-loading');  
    const resultsDiv = document.getElementById('results');  
    const answerContent = document.getElementById('answer-content');  
    const sourcesList = document.getElementById('sources-list');  
    const sourcesBox = document.getElementById('sources-box');  
    
    // Rebuild knowledge base related elements  
    const rebuildBtn = document.getElementById('rebuild-btn');  
    const rebuildLoading = document.getElementById('rebuild-loading');  
    const rebuildSuccess = document.getElementById('rebuild-success');  
    const rebuildError = document.getElementById('rebuild-error');  
    
    // Document list related elements  
    const refreshDocsBtn = document.getElementById('refresh-docs-btn');  
    const documentsLoading = document.getElementById('documents-loading');  
    const documentsList = document.getElementById('documents-list');  
    const noDocumentsMessage = document.getElementById('no-documents-message');  
    
    // System status  
    let isInitialized = false;  
    
    // Switch tabs  
    tabButtons.forEach(button => {  
        button.addEventListener('click', function() {  
            // Remove all active classes  
            tabButtons.forEach(btn => btn.classList.remove('active'));  
            tabPanes.forEach(pane => pane.classList.remove('active'));  
    
            // Add active class to current tab  
            button.classList.add('active');  
            const tabId = button.getAttribute('data-tab');  
            document.getElementById(tabId).classList.add('active');  
    
            // If switching to documents list tab, automatically refresh the list  
            if (tabId === 'documents') {  
                fetchDocuments();  
            }  
        });  
    });  
    
    // Get system information  
    async function fetchSystemInfo() {  
        try {  
            const response = await fetch('/api/info');  
            const data = await response.json();  
    
            if (data.status === 'success') {  
                modelInfoElement.textContent = `Model: ${data.model}  |  Embedding Model: ${data.embedding_model}  |  Threads: ${data.threads}`;  
                isInitialized = data.initialized;  
    
                // Show or hide warning based on initialization status  
                warningMessage.style.display = isInitialized ? 'none' : 'block';  
    
                // Disable or enable query button based on initialization status  
                queryBtn.disabled = !isInitialized;  
                if (!isInitialized) {  
                    queryBtn.style.backgroundColor = "#a0aec0";  
                } else {  
                    queryBtn.style.backgroundColor = "";  
                }  
            }  
        } catch (error) {  
            console.error('Failed to get system information:', error);  
            modelInfoElement.textContent = 'System connection failed';  
        }  
    }  
    
    // Stream query - using timed batch rendering  
    async function sendStreamQuery() {  
        const query = queryInput.value.trim();  
        if (!query) return;  
    
        // Clear previous results and show loading status  
        answerContent.innerHTML = '';  
        sourcesList.innerHTML = '';  
        sourcesBox.style.display = 'none';  
        queryLoading.style.display = 'flex';  
        resultsDiv.style.display = 'none';  
    
        // Store source document information but don't display immediately  
        let sourcesData = [];  
        
        // Buffer for storing Markdown text  
        let markdownBuffer = '';  
        
        // Timer-related variables for rendering  
        let renderTimer = null;  
        const RENDER_INTERVAL = 30; // milliseconds  
        
        // Add forced rendering timer  
        let forceRenderTimer = null;  
        const FORCE_RENDER_INTERVAL = 10; // Force render every 2 seconds to avoid long periods without rendering  
        
        // Timestamp of last render  
        let lastRenderTime = 0;  
        
        // Render function to avoid code duplication  
        function renderMarkdown() {  
            if (markdownBuffer.trim()) {  
                let processedMarkdown = markdownBuffer  
                    .replace(/<think>([\s\S]*?)<\/think>/g,   
                             '<div class="thinking-block">$1</div>')  
                             
                answerContent.innerHTML = marked.parse(processedMarkdown);  
                lastRenderTime = Date.now();  
            }   
        }  
        
        // Set up forced periodic rendering timer  
        function setupForceRenderTimer() {  
            forceRenderTimer = setInterval(() => {  
                // Force render if time since last render exceeds the forced interval  
                const now = Date.now();  
                if (now - lastRenderTime >= FORCE_RENDER_INTERVAL) {  
                    renderMarkdown();  
                }  
            }, FORCE_RENDER_INTERVAL);  
        }  
    
        try {  
            // Create SSE connection  
            const eventSource = new EventSource(`/api/query/stream?q=${encodeURIComponent(query)}`);  
            
            // Hide loading status and show results area when first message is received  
            let firstMessageReceived = false;  
            
            // Set up forced rendering timer  
            setupForceRenderTimer();  
            
            // Record initial render time  
            lastRenderTime = Date.now();  
    
            eventSource.onmessage = function(event) {  
                // First message handling  
                if (!firstMessageReceived) {  
                    queryLoading.style.display = 'none';  
                    resultsDiv.style.display = 'block';  
                    firstMessageReceived = true;  
                }  
    
                const data = JSON.parse(event.data);  
    
                if (data.type === 'token') {  
                    // Add token to buffer  
                    markdownBuffer += data.token;  
                    
                    // Clear previous render timer  
                    if (renderTimer) clearTimeout(renderTimer);  
                    
                    // Set new timer  
                    renderTimer = setTimeout(() => {  
                        renderMarkdown();  
                    }, RENDER_INTERVAL);  
                    
                }  
                else if (data.type === 'sources') {  
                    sourcesData = data.sources;  
                }  
                else if (data.type === 'error') {  
                    answerContent.innerHTML = `<div class="error-message">Error: ${data.error}</div>`;  
                    
                    // Clean up timers  
                    if (renderTimer) clearTimeout(renderTimer);  
                    if (forceRenderTimer) clearInterval(forceRenderTimer);  
                    
                    eventSource.close();  
                }  
                else if (data.type === 'end') {  
                    // Perform final render immediately when stream ends  
                    renderMarkdown();  
                    
                    // Clean up timers  
                    if (renderTimer) clearTimeout(renderTimer);  
                    if (forceRenderTimer) clearInterval(forceRenderTimer);  
                    
                    // Display source documents  
                    if (sourcesData.length > 0) {  
                        sourcesList.innerHTML = '';  
                        sourcesData.forEach((source, index) => {  
                            const sourceItem = document.createElement('div');  
                            sourceItem.className = 'source-item';  
    
                            const sourceTitle = document.createElement('div');  
                            sourceTitle.className = 'source-title';  
                            sourceTitle.textContent = `Source ${index + 1}: ${source.source}`;  
    
                            const sourceContent = document.createElement('div');  
                            sourceContent.className = 'source-content';  
                            sourceContent.textContent = source.content;  
    
                            sourceItem.appendChild(sourceTitle);  
                            sourceItem.appendChild(sourceContent);  
                            sourcesList.appendChild(sourceItem);  
                        });  
    
                        sourcesBox.style.display = 'block';  
                        setTimeout(() => {  
                            sourcesBox.classList.add('show');  
                        }, 10);  
                    }  
    
                    eventSource.close();  
                }  
            };  
    
            eventSource.onerror = function(error) {  
                console.error('EventSource error:', error);  
                queryLoading.style.display = 'none';  
                resultsDiv.style.display = 'block';  
                answerContent.innerHTML += '<div class="error-message">Connection error, please try again</div>';  
                
                // Clean up timers  
                if (renderTimer) clearTimeout(renderTimer);  
                if (forceRenderTimer) clearInterval(forceRenderTimer);  
                
                eventSource.close();  
            };  
    
        } catch (error) {  
            console.error('Query processing failed:', error);  
            queryLoading.style.display = 'none';  
            resultsDiv.style.display = 'block';  
            answerContent.innerHTML = `<div class="error-message">Query processing failed: ${error.message}</div>`;  
            
            // Ensure timers are cleaned up  
            if (renderTimer) clearTimeout(renderTimer);  
            if (forceRenderTimer) clearInterval(forceRenderTimer);  
        }  
    }  
    // Rebuild knowledge base  
    async function rebuildKnowledgeBase() {  
        // Show loading, hide messages  
        rebuildLoading.style.display = 'flex';  
        rebuildSuccess.style.display = 'none';  
        rebuildError.style.display = 'none';  
        rebuildBtn.disabled = true;  
    
        try {  
            const response = await fetch('/api/rebuild', {  
                method: 'POST'  
            });  
    
            const data = await response.json();  
    
            // Hide loading  
            rebuildLoading.style.display = 'none';  
            rebuildBtn.disabled = false;  
    
            if (data.status === 'success') {  
                rebuildSuccess.textContent = data.message;  
                rebuildSuccess.style.display = 'block';  
    
                // Refresh system information  
                fetchSystemInfo();  
            } else {  
                rebuildError.textContent = data.message;  
                rebuildError.style.display = 'block';  
            }  
        } catch (error) {  
            rebuildLoading.style.display = 'none';  
            rebuildBtn.disabled = false;  
            console.error('Failed to rebuild knowledge base:', error);  
    
            rebuildError.textContent = 'Failed to rebuild knowledge base, please check network connection';  
            rebuildError.style.display = 'block';  
        }  
    }  
    
    // Get document list  
    async function fetchDocuments() {  
        // Show loading, hide list and messages  
        documentsLoading.style.display = 'flex';  
        documentsList.innerHTML = '';  
        noDocumentsMessage.style.display = 'none';  
    
        try {  
            const response = await fetch('/api/documents');  
            const data = await response.json();  
    
            // Hide loading  
            documentsLoading.style.display = 'none';  
    
            if (data.status === 'success') {  
                if (data.documents && data.documents.length > 0) {  
                    data.documents.forEach(doc => {  
                        const docItem = document.createElement('div');  
                        docItem.className = 'document-item';  
    
                        // Simple file icon  
                        const docIcon = document.createElement('span');  
                        docIcon.className = 'document-icon';  
                        docIcon.innerHTML = '📄';  
    
                        const docName = document.createElement('span');  
                        docName.textContent = doc;  
    
                        docItem.appendChild(docIcon);  
                        docItem.appendChild(docName);  
                        documentsList.appendChild(docItem);  
                    });  
                } else {  
                    noDocumentsMessage.style.display = 'block';  
                }  
            } else {  
                alert(`Failed to get document list: ${data.message}`);  
            }  
        } catch (error) {  
            documentsLoading.style.display = 'none';  
            console.error('Failed to get document list:', error);  
            alert('Failed to get document list, please check network connection');  
        }  
    }  
    
    // Event listeners - only use streaming query  
    queryBtn.addEventListener('click', sendStreamQuery);  
    queryInput.addEventListener('keypress', function(e) {  
        if (e.key === 'Enter') sendStreamQuery();  
    });  
    
    rebuildBtn.addEventListener('click', rebuildKnowledgeBase);  
    refreshDocsBtn.addEventListener('click', fetchDocuments);  
    
    // Initialize page  
    fetchSystemInfo();  
});